"""
Core utilities for Gemini CLI subprocess execution.

This module provides the foundational functions for executing Gemini CLI commands
with proper error handling, retry logic, and output sanitization.
"""
import asyncio
import os
import re
import shutil
import time
import logging
from typing import Optional
from cachetools import TTLCache

logger = logging.getLogger(__name__)

# Configuration from environment
GEMINI_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT", "300"))
GEMINI_COMMAND_PATH = os.getenv("GEMINI_COMMAND_PATH", "gemini")
RETRY_MAX_ATTEMPTS = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
RETRY_BASE_DELAY = float(os.getenv("RETRY_BASE_DELAY", "1.0"))
RETRY_MAX_DELAY = float(os.getenv("RETRY_MAX_DELAY", "30.0"))

# Caches with TTL
HELP_CACHE: TTLCache = TTLCache(maxsize=1, ttl=1800)  # 30 min
VERSION_CACHE: TTLCache = TTLCache(maxsize=1, ttl=1800)  # 30 min
PROMPT_CACHE: TTLCache = TTLCache(maxsize=100, ttl=300)  # 5 min

# Metrics tracking
METRICS = {
    "commands_executed": 0,
    "commands_succeeded": 0,
    "commands_failed": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "total_execution_time": 0.0,
    "rate_limit_hits": 0,
    "fallback_count": 0,
    "start_time": time.time(),
}


class GeminiExecutionError(Exception):
    """Base exception for Gemini execution errors."""
    pass


class GeminiTimeoutError(GeminiExecutionError):
    """Raised when Gemini CLI command times out."""
    pass


class GeminiRateLimitError(GeminiExecutionError):
    """Raised when rate limits are exceeded."""
    pass


def validate_gemini_setup() -> bool:
    """Validate that Gemini CLI is properly installed and configured."""
    gemini_path = shutil.which(GEMINI_COMMAND_PATH)
    if not gemini_path:
        logger.error(f"Gemini CLI not found at: {GEMINI_COMMAND_PATH}")
        return False
    logger.info(f"Gemini CLI found at: {gemini_path}")
    return True


def sanitize_output(output: str) -> str:
    """
    Sanitize output to remove potentially sensitive information.

    Args:
        output: Raw output string from Gemini CLI

    Returns:
        Sanitized output string
    """
    # Remove potential API keys
    output = re.sub(r'AIza[0-9A-Za-z_-]{35}', '[REDACTED_API_KEY]', output)
    # Remove potential secrets
    output = re.sub(r'sk-[a-zA-Z0-9]{32,}', '[REDACTED_SECRET]', output)
    # Remove potential bearer tokens
    output = re.sub(r'Bearer\s+[a-zA-Z0-9._-]+', 'Bearer [REDACTED]', output)
    return output


def _build_gemini_args(
    command: Optional[str] = None,
    prompt: Optional[str] = None,
    model: Optional[str] = None,
    sandbox: bool = False,
    sandbox_image: Optional[str] = None,
    debug: bool = False,
    extra_args: Optional[list] = None
) -> list[str]:
    """Build argument list for Gemini CLI execution."""
    args = []

    if command:
        # Direct command - split by space but preserve quoted strings
        import shlex
        try:
            args.extend(shlex.split(command))
        except ValueError:
            args.extend(command.split())
    else:
        # Structured command building
        if model:
            args.extend(["--model", model])

        if sandbox:
            args.append("--sandbox")
            if sandbox_image:
                args.extend(["--sandbox-image", sandbox_image])

        if debug:
            args.append("--debug")

        if prompt:
            args.extend(["--prompt", prompt])

    if extra_args:
        args.extend(extra_args)

    return args


async def execute_gemini(
    args: list[str],
    timeout: Optional[int] = None,
    capture_stderr: bool = True
) -> dict:
    """
    Execute Gemini CLI command asynchronously.

    Args:
        args: Command line arguments for Gemini CLI
        timeout: Optional timeout in seconds (defaults to GEMINI_TIMEOUT)
        capture_stderr: Whether to capture stderr output

    Returns:
        Dictionary with status, stdout, stderr, and return_code

    Raises:
        GeminiTimeoutError: If command times out
        GeminiExecutionError: If command fails to execute
    """
    timeout = timeout or GEMINI_TIMEOUT
    start_time = time.time()

    METRICS["commands_executed"] += 1

    try:
        logger.debug(f"Executing: {GEMINI_COMMAND_PATH} {' '.join(args)}")

        process = await asyncio.create_subprocess_exec(
            GEMINI_COMMAND_PATH,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE if capture_stderr else None,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            METRICS["commands_failed"] += 1
            raise GeminiTimeoutError(
                f"Command timed out after {timeout} seconds"
            )

        execution_time = time.time() - start_time
        METRICS["total_execution_time"] += execution_time

        stdout_str = sanitize_output(stdout.decode("utf-8", errors="replace"))
        stderr_str = sanitize_output(
            stderr.decode("utf-8", errors="replace") if stderr else ""
        )

        # Check for rate limiting
        if "rate limit" in stderr_str.lower() or "quota" in stderr_str.lower():
            METRICS["rate_limit_hits"] += 1
            raise GeminiRateLimitError(f"Rate limit exceeded: {stderr_str}")

        if process.returncode == 0:
            METRICS["commands_succeeded"] += 1
            return {
                "status": "success",
                "return_code": process.returncode,
                "stdout": stdout_str,
                "stderr": stderr_str,
                "execution_time": execution_time
            }
        else:
            METRICS["commands_failed"] += 1
            return {
                "status": "error",
                "return_code": process.returncode,
                "stdout": stdout_str,
                "stderr": stderr_str,
                "execution_time": execution_time
            }

    except (GeminiTimeoutError, GeminiRateLimitError):
        raise
    except FileNotFoundError:
        METRICS["commands_failed"] += 1
        raise GeminiExecutionError(
            f"Gemini CLI not found at: {GEMINI_COMMAND_PATH}. "
            "Please ensure Gemini CLI is installed and in PATH."
        )
    except Exception as e:
        METRICS["commands_failed"] += 1
        logger.error(f"Unexpected error executing Gemini CLI: {e}")
        raise GeminiExecutionError(f"Execution failed: {str(e)}")


async def execute_gemini_with_retry(
    args: list[str],
    timeout: Optional[int] = None,
    max_attempts: Optional[int] = None,
    fallback_model: Optional[str] = None
) -> dict:
    """
    Execute Gemini CLI with exponential backoff retry.

    Args:
        args: Command line arguments for Gemini CLI
        timeout: Optional timeout in seconds
        max_attempts: Maximum retry attempts (defaults to RETRY_MAX_ATTEMPTS)
        fallback_model: Optional fallback model if primary fails

    Returns:
        Dictionary with execution results
    """
    max_attempts = max_attempts or RETRY_MAX_ATTEMPTS
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            return await execute_gemini(args, timeout)

        except GeminiRateLimitError as e:
            last_error = e

            # Try fallback model if available
            if fallback_model and "--model" in args:
                model_idx = args.index("--model")
                original_model = args[model_idx + 1]
                args[model_idx + 1] = fallback_model
                METRICS["fallback_count"] += 1
                logger.info(
                    f"Falling back from {original_model} to {fallback_model}"
                )
                try:
                    return await execute_gemini(args, timeout)
                except Exception:
                    args[model_idx + 1] = original_model

            if attempt < max_attempts:
                # Exponential backoff with jitter
                delay = min(
                    RETRY_BASE_DELAY * (2 ** (attempt - 1)),
                    RETRY_MAX_DELAY
                )
                import random
                delay += random.uniform(0, delay * 0.1)
                logger.warning(
                    f"Rate limit hit, attempt {attempt}/{max_attempts}. "
                    f"Retrying in {delay:.1f}s"
                )
                await asyncio.sleep(delay)

        except GeminiTimeoutError as e:
            last_error = e
            if attempt < max_attempts:
                logger.warning(
                    f"Timeout on attempt {attempt}/{max_attempts}, retrying..."
                )

        except GeminiExecutionError as e:
            last_error = e
            # Don't retry for non-transient errors
            break

    raise last_error or GeminiExecutionError("All retry attempts failed")


async def get_gemini_help() -> str:
    """Get Gemini CLI help with caching."""
    cache_key = "help"

    if cache_key in HELP_CACHE:
        METRICS["cache_hits"] += 1
        return HELP_CACHE[cache_key]

    METRICS["cache_misses"] += 1
    result = await execute_gemini(["--help"], timeout=30)

    output = result["stdout"] if result["status"] == "success" else result["stderr"]
    HELP_CACHE[cache_key] = output
    return output


async def get_gemini_version() -> str:
    """Get Gemini CLI version with caching."""
    cache_key = "version"

    if cache_key in VERSION_CACHE:
        METRICS["cache_hits"] += 1
        return VERSION_CACHE[cache_key]

    METRICS["cache_misses"] += 1
    result = await execute_gemini(["--version"], timeout=30)

    output = result["stdout"] if result["status"] == "success" else result["stderr"]
    VERSION_CACHE[cache_key] = output
    return output


def get_metrics() -> dict:
    """Get current metrics."""
    uptime = time.time() - METRICS["start_time"]
    total_commands = METRICS["commands_executed"]

    return {
        **METRICS,
        "uptime_seconds": uptime,
        "success_rate": (
            METRICS["commands_succeeded"] / total_commands * 100
            if total_commands > 0 else 0
        ),
        "average_execution_time": (
            METRICS["total_execution_time"] / total_commands
            if total_commands > 0 else 0
        ),
        "cache_hit_rate": (
            METRICS["cache_hits"] /
            (METRICS["cache_hits"] + METRICS["cache_misses"]) * 100
            if (METRICS["cache_hits"] + METRICS["cache_misses"]) > 0 else 0
        ),
    }
