"""
Specialized code review and analysis tools.

This module implements the gemini_code_review, gemini_extract_structured,
and gemini_git_diff_review tools.
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
    GEMINI_CODE_REVIEW_LIMIT,
    GEMINI_EXTRACT_STRUCTURED_LIMIT,
    GEMINI_GIT_DIFF_LIMIT,
    FALLBACK_MODEL,
    get_model_scaling_factor,
)

logger = logging.getLogger(__name__)


async def execute_code_review(
    code: str,
    language: Optional[str] = None,
    focus_areas: Optional[str] = None,
    severity_threshold: str = "info",
    output_format: str = "structured"
) -> str:
    """
    Execute a comprehensive code review with structured output.

    Args:
        code: Code to review
        language: Programming language
        focus_areas: Comma-separated focus areas
        severity_threshold: Minimum severity to report
        output_format: Output format

    Returns:
        JSON string with code review results
    """
    model = "gemini-2.5-pro"
    scaling_factor = get_model_scaling_factor(model)
    effective_limit = int(GEMINI_CODE_REVIEW_LIMIT * scaling_factor)

    if len(code) > effective_limit:
        return json.dumps({
            "status": "error",
            "error": f"Code exceeds limit of {effective_limit:,} characters",
            "error_code": "INPUT_TOO_LARGE"
        })

    try:
        from prompts.code_review_template import get_structured_code_review_prompt
        prompt = get_structured_code_review_prompt(
            code=code,
            language=language,
            focus_areas=focus_areas,
            severity_threshold=severity_threshold,
            output_format=output_format
        )
    except ImportError:
        # Fallback prompt
        focus_text = f"\n\nFocus areas: {focus_areas}" if focus_areas else ""
        lang_text = f"\n\nLanguage: {language}" if language else ""
        prompt = f"""Perform a comprehensive code review.{focus_text}{lang_text}

Code:
{code}

Provide analysis in {output_format} format with severity levels."""

    args = ["--model", model, "--prompt", prompt]

    try:
        result = await execute_gemini_with_retry(args, fallback_model=FALLBACK_MODEL)
        return json.dumps(result, indent=2)
    except (GeminiTimeoutError, GeminiRateLimitError, GeminiExecutionError) as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        })


async def execute_extract_structured(
    content: str,
    schema: str,
    examples: Optional[str] = None,
    strict_mode: bool = True,
    model: Optional[str] = None
) -> str:
    """
    Extract structured data using JSON schemas.

    Args:
        content: Content to analyze
        schema: JSON schema for output
        examples: Optional examples
        strict_mode: Enforce strict schema compliance
        model: Model to use

    Returns:
        JSON string with extracted data
    """
    model = model or "gemini-2.5-flash"
    scaling_factor = get_model_scaling_factor(model)
    effective_limit = int(GEMINI_EXTRACT_STRUCTURED_LIMIT * scaling_factor)

    total_length = len(content) + len(schema) + len(examples or "")
    if total_length > effective_limit:
        return json.dumps({
            "status": "error",
            "error": f"Input exceeds limit of {effective_limit:,} characters",
            "error_code": "INPUT_TOO_LARGE"
        })

    # Validate schema is valid JSON
    try:
        json.loads(schema)
    except json.JSONDecodeError as e:
        return json.dumps({
            "status": "error",
            "error": f"Invalid JSON schema: {str(e)}",
            "error_code": "INVALID_SCHEMA"
        })

    try:
        from prompts.extract_structured_template import get_extract_structured_prompt
        prompt = get_extract_structured_prompt(
            content=content,
            schema=schema,
            examples=examples,
            strict_mode=strict_mode
        )
    except ImportError:
        strict_text = " Strictly follow the schema." if strict_mode else ""
        example_text = f"\n\nExamples:\n{examples}" if examples else ""
        prompt = f"""Extract structured data from the following content according to this schema.{strict_text}

Schema:
{schema}{example_text}

Content:
{content}

Return valid JSON matching the schema."""

    args = ["--model", model, "--prompt", prompt]

    try:
        result = await execute_gemini_with_retry(args, fallback_model=FALLBACK_MODEL)
        return json.dumps(result, indent=2)
    except (GeminiTimeoutError, GeminiRateLimitError, GeminiExecutionError) as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        })


async def execute_git_diff_review(
    diff: str,
    context_lines: int = 3,
    review_type: str = "comprehensive",
    base_branch: Optional[str] = None,
    commit_message: Optional[str] = None
) -> str:
    """
    Analyze git diffs with contextual feedback.

    Args:
        diff: Git diff content
        context_lines: Number of context lines
        review_type: Type of review
        base_branch: Base branch
        commit_message: Commit message

    Returns:
        JSON string with diff analysis
    """
    model = "gemini-2.5-pro"
    scaling_factor = get_model_scaling_factor(model)
    effective_limit = int(GEMINI_GIT_DIFF_LIMIT * scaling_factor)

    if len(diff) > effective_limit:
        return json.dumps({
            "status": "error",
            "error": f"Diff exceeds limit of {effective_limit:,} characters",
            "error_code": "INPUT_TOO_LARGE"
        })

    try:
        from prompts.git_diff_review_template import get_git_diff_review_prompt
        prompt = get_git_diff_review_prompt(
            diff=diff,
            context_lines=context_lines,
            review_type=review_type,
            base_branch=base_branch,
            commit_message=commit_message
        )
    except ImportError:
        branch_text = f"\n\nBase branch: {base_branch}" if base_branch else ""
        commit_text = f"\n\nCommit message: {commit_message}" if commit_message else ""
        prompt = f"""Review the following git diff ({review_type} review).{branch_text}{commit_text}

Diff:
{diff}

Provide feedback on:
1. Code quality changes
2. Potential issues introduced
3. Security implications
4. Suggestions for improvement"""

    args = ["--model", model, "--prompt", prompt]

    try:
        result = await execute_gemini_with_retry(args, fallback_model=FALLBACK_MODEL)
        return json.dumps(result, indent=2)
    except (GeminiTimeoutError, GeminiRateLimitError, GeminiExecutionError) as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        })
