"""
Plan evaluation templates.

This module provides templates for the gemini_eval_plan tool.
"""
from typing import Optional
from .base_template import BaseTemplate


def get_eval_plan_prompt(
    plan: str,
    context: Optional[str] = None,
    requirements: Optional[str] = None
) -> str:
    """
    Generate a plan evaluation prompt.

    Args:
        plan: The implementation plan to evaluate
        context: Optional context information
        requirements: Optional requirements

    Returns:
        Complete prompt string
    """
    context_section = ""
    if context:
        context_section = f"""

Context:
{context}
"""

    requirements_section = ""
    if requirements:
        requirements_section = f"""

Requirements:
{requirements}
"""

    return f"""Please evaluate the following implementation plan for completeness, correctness, and potential issues.{context_section}{requirements_section}

Plan:
{plan}

Please provide a detailed analysis including:

## 1. Plan Assessment

### Completeness Score: [1-10]
- Does the plan cover all necessary components?
- Are there any obvious gaps?

### Feasibility Score: [1-10]
- Is the plan technically feasible?
- Are there any unrealistic expectations?

### Risk Level: [Low/Medium/High]
- What is the overall risk level?

## 2. Strengths
- What does the plan do well?
- What are the strongest aspects?

## 3. Potential Issues
- What problems might arise?
- What edge cases are not addressed?

## 4. Missing Considerations
- What has been overlooked?
- What dependencies are not mentioned?

## 5. Security Analysis
- Are there security implications?
- What vulnerabilities might be introduced?

## 6. Performance Considerations
- How might this impact performance?
- Are there scalability concerns?

## 7. Recommendations
- Specific improvements to the plan
- Priority ordering of changes

## 8. Alternative Approaches
- Are there better ways to achieve the goals?
- What trade-offs should be considered?

## 9. Implementation Notes
- Suggested implementation order
- Key decision points

## 10. Summary
- Overall assessment (2-3 sentences)
- Go/No-Go recommendation with justification"""


class EvalTemplate(BaseTemplate):
    """Template class for plan evaluation prompts."""

    @staticmethod
    def get_prompt(
        plan: str,
        context: Optional[str] = None,
        requirements: Optional[str] = None
    ) -> str:
        """Get the plan evaluation prompt."""
        return get_eval_plan_prompt(plan, context, requirements)
