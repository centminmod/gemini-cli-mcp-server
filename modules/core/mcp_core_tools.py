"""
Pure MCP tool implementations for core Gemini CLI tools.

This module contains the core implementations that are imported by mcp_server.py.
"""
import json
import logging
from typing import Optional

from modules.utils.gemini_utils import (
    execute_gemini_with_retry,
    GeminiExecutionError,
    GeminiTimeoutError,
    GeminiRateLimitError,
)
from modules.config.gemini_config import (
    GEMINI_PROMPT_LIMIT,
    DEFAULT_MODEL,
    FALLBACK_MODEL,
    get_model_scaling_factor,
)

logger = logging.getLogger(__name__)


async def execute_prompt(
    prompt: str,
    model: Optional[str] = None,
    sandbox: bool = False,
    debug: bool = False
) -> dict:
    """
    Execute a prompt with the Gemini CLI.

    Args:
        prompt: The prompt to send
        model: Model to use
        sandbox: Whether to use sandbox mode
        debug: Whether to enable debug output

    Returns:
        Execution result dictionary
    """
    model = model or DEFAULT_MODEL
    scaling_factor = get_model_scaling_factor(model)
    effective_limit = int(GEMINI_PROMPT_LIMIT * scaling_factor)

    if len(prompt) > effective_limit:
        return {
            "status": "error",
            "error": f"Prompt exceeds limit of {effective_limit:,} characters",
            "error_code": "INPUT_TOO_LARGE"
        }

    args = []
    if model:
        args.extend(["--model", model])
    if sandbox:
        args.append("--sandbox")
    if debug:
        args.append("--debug")
    args.extend(["--prompt", prompt])

    try:
        result = await execute_gemini_with_retry(
            args,
            fallback_model=FALLBACK_MODEL if model != FALLBACK_MODEL else None
        )
        return result
    except GeminiTimeoutError as e:
        return {"status": "error", "error": str(e), "error_code": "TIMEOUT"}
    except GeminiRateLimitError as e:
        return {"status": "error", "error": str(e), "error_code": "RATE_LIMIT"}
    except GeminiExecutionError as e:
        return {"status": "error", "error": str(e), "error_code": "EXECUTION_ERROR"}
    except Exception as e:
        logger.error(f"Unexpected error in execute_prompt: {e}")
        return {"status": "error", "error": str(e), "error_code": "INTERNAL_ERROR"}


def validate_prompt_length(prompt: str, limit: int, model: str = None) -> tuple[bool, str]:
    """
    Validate that a prompt is within the allowed length.

    Args:
        prompt: The prompt to validate
        limit: Base character limit
        model: Optional model for scaling

    Returns:
        Tuple of (is_valid, error_message)
    """
    scaling_factor = get_model_scaling_factor(model) if model else 1.0
    effective_limit = int(limit * scaling_factor)

    if len(prompt) > effective_limit:
        return False, f"Input exceeds limit of {effective_limit:,} characters (got {len(prompt):,})"

    return True, ""


def build_prompt_with_context(
    base_prompt: str,
    context: Optional[str] = None,
    requirements: Optional[str] = None,
    additional_params: Optional[dict] = None
) -> str:
    """
    Build a full prompt with optional context and requirements.

    Args:
        base_prompt: The main prompt content
        context: Optional context information
        requirements: Optional requirements
        additional_params: Additional parameters to include

    Returns:
        Complete prompt string
    """
    parts = [base_prompt]

    if context:
        parts.append(f"\n\nContext:\n{context}")

    if requirements:
        parts.append(f"\n\nRequirements:\n{requirements}")

    if additional_params:
        for key, value in additional_params.items():
            if value:
                parts.append(f"\n\n{key.replace('_', ' ').title()}:\n{value}")

    return "".join(parts)
