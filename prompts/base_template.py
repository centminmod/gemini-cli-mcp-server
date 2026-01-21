"""
Base template class and common template utilities.

This module provides the base class for all templates and common utilities.
"""
from typing import Optional


class BaseTemplate:
    """Base class for prompt templates."""

    @staticmethod
    def format_section(title: str, content: Optional[str]) -> str:
        """Format an optional section."""
        if not content:
            return ""
        return f"\n\n{title}:\n{content}"

    @staticmethod
    def format_list(items: list, numbered: bool = True) -> str:
        """Format a list of items."""
        if not items:
            return ""

        if numbered:
            return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1))
        return "\n".join(f"- {item}" for item in items)

    @staticmethod
    def format_code_block(code: str, language: Optional[str] = None) -> str:
        """Format code in a code block."""
        lang = language or ""
        return f"```{lang}\n{code}\n```"

    @staticmethod
    def truncate(text: str, max_length: int = 500) -> str:
        """Truncate text with ellipsis."""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."


# Common prompt components
ANALYSIS_COMPONENTS = {
    "strengths": "Strengths and positive aspects",
    "weaknesses": "Weaknesses and areas for improvement",
    "risks": "Potential risks and concerns",
    "recommendations": "Recommendations for improvement",
    "summary": "Executive summary",
}

CODE_REVIEW_ASPECTS = {
    "correctness": "Code correctness and logic",
    "security": "Security vulnerabilities and concerns",
    "performance": "Performance implications",
    "maintainability": "Code maintainability and readability",
    "best_practices": "Best practices compliance",
    "testing": "Test coverage and testability",
}

SEVERITY_LEVELS = {
    "critical": "Issues that must be addressed immediately",
    "error": "Significant issues that should be fixed",
    "warning": "Potential issues or improvements",
    "info": "Informational suggestions",
}
