"""
Content summarization templates.

This module provides templates for the gemini_summarize and gemini_summarize_files tools.
"""
from typing import Optional
from .base_template import BaseTemplate


def get_summarize_prompt(content: str, focus: Optional[str] = None) -> str:
    """
    Generate a summarization prompt.

    Args:
        content: Content to summarize
        focus: Optional focus area

    Returns:
        Complete prompt string
    """
    focus_section = ""
    if focus:
        focus_section = f"""

Focus Area:
Please pay particular attention to: {focus}
"""

    return f"""Please provide a comprehensive summary of the following content.{focus_section}

Content:
{content}

Please structure your summary as follows:

1. **Executive Summary** (2-3 sentences)
   - Key takeaway points

2. **Main Points**
   - Primary themes and concepts
   - Important details

3. **Key Findings** (if applicable)
   - Notable discoveries or insights
   - Critical information

4. **Structure/Organization** (if code or technical content)
   - How the content is organized
   - Dependencies and relationships

5. **Recommendations** (if applicable)
   - Suggested next steps
   - Areas for further investigation"""


def get_summarize_files_prompt(files: str, focus: Optional[str] = None) -> str:
    """
    Generate a file summarization prompt optimized for @filename syntax.

    Args:
        files: File specifications using @filename syntax
        focus: Optional focus area

    Returns:
        Complete prompt string
    """
    focus_section = ""
    if focus:
        focus_section = f"\n\nFocus Area: {focus}"

    return f"""Analyze and summarize the following files.{focus_section}

Files:
{files}

Please provide:

1. **Overview**
   - Purpose of each file/directory
   - Overall architecture

2. **Key Components**
   - Main functions/classes
   - Important modules

3. **Dependencies**
   - Internal dependencies
   - External dependencies

4. **Patterns & Practices**
   - Design patterns used
   - Code organization

5. **Summary**
   - Key insights
   - Recommendations"""


class SummarizeTemplate(BaseTemplate):
    """Template class for summarization prompts."""

    @staticmethod
    def get_prompt(content: str, focus: Optional[str] = None) -> str:
        """Get the summarization prompt."""
        return get_summarize_prompt(content, focus)

    @staticmethod
    def get_files_prompt(files: str, focus: Optional[str] = None) -> str:
        """Get the file summarization prompt."""
        return get_summarize_files_prompt(files, focus)
