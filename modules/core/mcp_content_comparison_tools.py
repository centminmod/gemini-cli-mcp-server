"""
Multi-source content comparison capabilities.

This module implements the gemini_content_comparison tool.
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
    GEMINI_CONTENT_COMPARISON_LIMIT,
    FALLBACK_MODEL,
    get_model_scaling_factor,
)

logger = logging.getLogger(__name__)


async def execute_content_comparison(
    sources: str,
    comparison_type: str = "semantic",
    output_format: str = "structured",
    include_metrics: bool = True,
    focus_areas: Optional[str] = None
) -> str:
    """
    Execute advanced multi-source content comparison.

    Args:
        sources: JSON array of sources to compare
        comparison_type: Type of comparison (semantic, textual, structural, factual, code)
        output_format: Output format (structured, matrix, summary, detailed, json)
        include_metrics: Include similarity scores
        focus_areas: Focus areas for comparison

    Returns:
        JSON string with comparison results
    """
    model = "gemini-2.5-pro"
    scaling_factor = get_model_scaling_factor(model)
    effective_limit = int(GEMINI_CONTENT_COMPARISON_LIMIT * scaling_factor)

    if len(sources) > effective_limit:
        return json.dumps({
            "status": "error",
            "error": f"Sources exceed limit of {effective_limit:,} characters",
            "error_code": "INPUT_TOO_LARGE"
        })

    # Validate sources is valid JSON array
    try:
        sources_list = json.loads(sources)
        if not isinstance(sources_list, list):
            raise ValueError("Sources must be a JSON array")
        if len(sources_list) < 2:
            return json.dumps({
                "status": "error",
                "error": "At least 2 sources required for comparison",
                "error_code": "INSUFFICIENT_SOURCES"
            })
    except (json.JSONDecodeError, ValueError) as e:
        return json.dumps({
            "status": "error",
            "error": f"Invalid sources format: {str(e)}",
            "error_code": "INVALID_SOURCES"
        })

    try:
        from prompts.content_comparison_template import get_content_comparison_prompt
        prompt = get_content_comparison_prompt(
            sources=sources,
            comparison_type=comparison_type,
            output_format=output_format,
            include_metrics=include_metrics,
            focus_areas=focus_areas
        )
    except ImportError:
        focus_text = f"\n\nFocus on: {focus_areas}" if focus_areas else ""
        prompt = f"""Compare the following sources using {comparison_type} comparison.{focus_text}

Sources:
{sources}

Provide a {output_format} comparison{"with similarity metrics" if include_metrics else ""}."""

    args = ["--model", model, "--prompt", prompt]

    try:
        result = await execute_gemini_with_retry(args, fallback_model=FALLBACK_MODEL)
        return json.dumps(result, indent=2)
    except (GeminiTimeoutError, GeminiRateLimitError, GeminiExecutionError) as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        })


def parse_comparison_sources(sources_str: str) -> list:
    """
    Parse and validate comparison sources.

    Args:
        sources_str: JSON string of sources

    Returns:
        List of source specifications
    """
    try:
        sources = json.loads(sources_str)
        if not isinstance(sources, list):
            return []
        return sources
    except json.JSONDecodeError:
        return []


def categorize_source(source: str) -> str:
    """
    Categorize a source by type.

    Args:
        source: Source specification

    Returns:
        Source type (file, url, text)
    """
    if source.startswith("@"):
        return "file"
    elif source.startswith("http://") or source.startswith("https://"):
        return "url"
    else:
        return "text"
