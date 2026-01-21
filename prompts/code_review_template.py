"""
Structured code review templates.

This module provides templates for the gemini_code_review tool.
"""
from typing import Optional
from .base_template import BaseTemplate


def get_structured_code_review_prompt(
    code: str,
    language: Optional[str] = None,
    focus_areas: Optional[str] = None,
    severity_threshold: str = "info",
    output_format: str = "structured"
) -> str:
    """
    Generate a structured code review prompt.

    Args:
        code: Code to review
        language: Programming language
        focus_areas: Comma-separated focus areas
        severity_threshold: Minimum severity to report
        output_format: Output format

    Returns:
        Complete prompt string
    """
    language_section = f"\nLanguage: {language}" if language else ""

    focus_section = ""
    if focus_areas:
        areas = focus_areas.split(",")
        focus_section = f"\n\nFocus Areas:\n" + "\n".join(f"- {area.strip()}" for area in areas)

    format_instructions = {
        "structured": """
Output Format: Structured
- Use clear sections and subsections
- Provide severity ratings for each issue
- Include code references""",
        "markdown": """
Output Format: Markdown
- Use markdown formatting
- Include code blocks for examples
- Use tables where appropriate""",
        "json": """
Output Format: JSON
- Return a valid JSON object
- Include arrays for multiple items
- Use consistent key naming"""
    }.get(output_format, "")

    return f"""Perform a comprehensive code review with structured output.{language_section}{focus_section}

Severity Threshold: Only report issues at {severity_threshold} level or above.
{format_instructions}

Code:
{code}

Please analyze and provide:

## Analysis Summary
- Overall quality score (1-10)
- Total issues found by severity

## Issues Found

For each issue:
- Severity: [critical/error/warning/info]
- Category: [security/performance/quality/best_practices/documentation]
- Location: [file:line or description]
- Issue: [description]
- Recommendation: [fix]
- Code Example: [if applicable]

## Metrics
- Complexity score
- Maintainability index
- Test coverage estimate

## Recommendations
Prioritized list of improvements

## Summary
Brief overall assessment"""


class CodeReviewTemplate(BaseTemplate):
    """Template class for structured code review."""

    @staticmethod
    def get_prompt(
        code: str,
        language: Optional[str] = None,
        focus_areas: Optional[str] = None,
        severity_threshold: str = "info",
        output_format: str = "structured"
    ) -> str:
        """Get the structured code review prompt."""
        return get_structured_code_review_prompt(
            code, language, focus_areas, severity_threshold, output_format
        )
