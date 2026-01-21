"""
Code review templates.

This module provides templates for the gemini_review_code tool.
"""
from typing import Optional
from .base_template import BaseTemplate


def get_review_code_prompt(
    code: str,
    purpose: Optional[str] = None,
    context: Optional[str] = None,
    language: Optional[str] = None
) -> str:
    """
    Generate a code review prompt.

    Args:
        code: Code to review
        purpose: Purpose of the review
        context: Additional context
        language: Programming language

    Returns:
        Complete prompt string
    """
    purpose_section = ""
    if purpose:
        purpose_section = f"""

Review Purpose:
{purpose}
"""

    context_section = ""
    if context:
        context_section = f"""

Context:
{context}
"""

    language_section = ""
    if language:
        language_section = f"""

Programming Language: {language}
"""

    return f"""Please perform a comprehensive code review.{purpose_section}{context_section}{language_section}

Code:
{code}

Please analyze the code and provide feedback in the following structure:

## 1. Overview
- Brief description of what the code does
- Overall quality assessment [Excellent/Good/Acceptable/Needs Work/Poor]

## 2. Code Quality Analysis

### 2.1 Correctness
- Logic errors or bugs
- Edge cases not handled
- Potential runtime errors

### 2.2 Security
- Vulnerability assessment
- Input validation issues
- Authentication/authorization concerns
- Data exposure risks

### 2.3 Performance
- Efficiency concerns
- Algorithm complexity
- Resource usage
- Potential bottlenecks

### 2.4 Maintainability
- Code organization
- Naming conventions
- Documentation quality
- Complexity metrics

### 2.5 Best Practices
- Language-specific best practices
- Design pattern usage
- Code style consistency

## 3. Specific Issues

For each issue found, provide:
| Severity | Location | Issue | Recommendation |
|----------|----------|-------|----------------|
| [Critical/High/Medium/Low/Info] | [Line/Function] | [Description] | [Fix] |

## 4. Positive Aspects
- What the code does well
- Good patterns or practices observed

## 5. Recommendations

### Must Fix (Critical/High severity)
- Numbered list of critical fixes

### Should Fix (Medium severity)
- Numbered list of important improvements

### Consider (Low/Info severity)
- Numbered list of suggestions

## 6. Summary
- Overall verdict
- Key action items
- Estimated effort for improvements"""


class ReviewTemplate(BaseTemplate):
    """Template class for code review prompts."""

    @staticmethod
    def get_prompt(
        code: str,
        purpose: Optional[str] = None,
        context: Optional[str] = None,
        language: Optional[str] = None
    ) -> str:
        """Get the code review prompt."""
        return get_review_code_prompt(code, purpose, context, language)
