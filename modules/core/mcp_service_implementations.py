"""
System and service tools coordination layer.

This module implements system-level tools like sandbox execution,
cache management, and rate limiting statistics.
"""
import json
import logging
from typing import Optional

from modules.utils.gemini_utils import (
    execute_gemini_with_retry,
    get_metrics,
    HELP_CACHE,
    VERSION_CACHE,
    PROMPT_CACHE,
    GeminiExecutionError,
    GeminiTimeoutError,
    GeminiRateLimitError,
)
from modules.config.gemini_config import (
    GEMINI_SANDBOX_LIMIT,
    FALLBACK_MODEL,
    get_model_scaling_factor,
)

logger = logging.getLogger(__name__)


async def execute_sandbox(
    prompt: str,
    model: Optional[str] = None,
    sandbox_image: Optional[str] = None
) -> dict:
    """
    Execute a prompt in sandbox mode.

    Args:
        prompt: The prompt to execute
        model: Model to use (defaults to gemini-2.5-pro)
        sandbox_image: Optional Docker image for sandbox

    Returns:
        Execution result dictionary
    """
    model = model or "gemini-2.5-pro"
    scaling_factor = get_model_scaling_factor(model)
    effective_limit = int(GEMINI_SANDBOX_LIMIT * scaling_factor)

    if len(prompt) > effective_limit:
        return {
            "status": "error",
            "error": f"Prompt exceeds limit of {effective_limit:,} characters",
            "error_code": "INPUT_TOO_LARGE"
        }

    args = ["--model", model, "--sandbox"]
    if sandbox_image:
        args.extend(["--sandbox-image", sandbox_image])
    args.extend(["--prompt", prompt])

    try:
        result = await execute_gemini_with_retry(args, fallback_model=FALLBACK_MODEL)
        return result
    except (GeminiTimeoutError, GeminiRateLimitError, GeminiExecutionError) as e:
        error_code = type(e).__name__.replace("Gemini", "").replace("Error", "").upper()
        return {"status": "error", "error": str(e), "error_code": error_code}


def get_cache_statistics() -> dict:
    """
    Get comprehensive cache statistics.

    Returns:
        Dictionary with cache statistics for all caches
    """
    stats = {
        "help_cache": {
            "size": len(HELP_CACHE),
            "maxsize": HELP_CACHE.maxsize,
            "ttl_seconds": HELP_CACHE.ttl,
            "items": list(HELP_CACHE.keys())
        },
        "version_cache": {
            "size": len(VERSION_CACHE),
            "maxsize": VERSION_CACHE.maxsize,
            "ttl_seconds": VERSION_CACHE.ttl,
            "items": list(VERSION_CACHE.keys())
        },
        "prompt_cache": {
            "size": len(PROMPT_CACHE),
            "maxsize": PROMPT_CACHE.maxsize,
            "ttl_seconds": PROMPT_CACHE.ttl,
            "item_count": len(PROMPT_CACHE)
        }
    }

    # Add Redis cache stats if available
    try:
        from modules.services.redis_cache import get_redis_stats
        stats["redis_cache"] = get_redis_stats()
    except ImportError:
        stats["redis_cache"] = {"status": "not_configured"}

    return stats


def get_rate_limiting_statistics() -> dict:
    """
    Get comprehensive rate limiting statistics.

    Returns:
        Dictionary with rate limiting statistics
    """
    metrics = get_metrics()

    rate_stats = {
        "rate_limit_hits": metrics.get("rate_limit_hits", 0),
        "fallback_count": metrics.get("fallback_count", 0),
        "commands_executed": metrics.get("commands_executed", 0),
        "success_rate": metrics.get("success_rate", 0),
    }

    # Add per-model rate limiting stats if available
    try:
        from modules.services.per_model_rate_limiter import get_rate_limit_stats
        rate_stats["per_model_stats"] = get_rate_limit_stats()
    except ImportError:
        rate_stats["per_model_stats"] = {"status": "not_configured"}

    return rate_stats


def get_server_metrics() -> dict:
    """
    Get comprehensive server metrics.

    Returns:
        Dictionary with server metrics
    """
    metrics = get_metrics()
    cache_stats = get_cache_statistics()

    return {
        "metrics": metrics,
        "cache_stats": cache_stats,
        "server_info": {
            "name": "gemini-cli-mcp-server",
            "tools_available": 33,
        }
    }
