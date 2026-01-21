"""
Sequential pipeline collaboration templates.

This module provides templates for sequential mode in gemini_ai_collaboration.
"""
from typing import Optional
from .base_template import BaseTemplate


def get_sequential_stage_prompt(
    content: str,
    stage_name: str,
    stage_number: int,
    total_stages: int,
    previous_output: Optional[str] = None,
    focus: Optional[str] = None
) -> str:
    """
    Generate a sequential pipeline stage prompt.

    Args:
        content: Content to analyze
        stage_name: Name of current stage
        stage_number: Current stage number
        total_stages: Total number of stages
        previous_output: Output from previous stage
        focus: Focus area

    Returns:
        Stage prompt string
    """
    previous_section = ""
    if previous_output:
        previous_section = f"""

Previous Stage Output:
{previous_output}
"""

    focus_section = ""
    if focus:
        focus_section = f"\nFocus: {focus}"

    stage_instructions = {
        "analysis": """
Stage: Analysis
- Examine the content thoroughly
- Identify key components
- Note areas requiring attention""",
        "security_review": """
Stage: Security Review
- Identify vulnerabilities
- Check for security best practices
- Recommend security improvements""",
        "optimization": """
Stage: Optimization
- Identify performance issues
- Suggest optimizations
- Prioritize improvements""",
        "final_validation": """
Stage: Final Validation
- Verify all requirements met
- Check for completeness
- Provide final assessment""",
        "code_review": """
Stage: Code Review
- Review code quality
- Check for bugs
- Assess maintainability""",
        "documentation": """
Stage: Documentation
- Review/generate documentation
- Ensure completeness
- Check accuracy"""
    }.get(stage_name.lower().replace(" ", "_"), f"Stage: {stage_name}")

    return f"""You are stage {stage_number} of {total_stages} in a sequential analysis pipeline.
{stage_instructions}{focus_section}{previous_section}

Content:
{content}

Instructions:
1. Perform your stage-specific analysis
2. Build upon the previous stage output (if any)
3. Provide clear findings and recommendations
4. Format output for the next stage

Please provide your output:

## {stage_name} Results

### Findings
[Your analysis findings]

### Issues Identified
| Priority | Issue | Recommendation |
|----------|-------|----------------|
| [High/Medium/Low] | [Description] | [Fix] |

### Recommendations
1. [Recommendation 1]
2. [Recommendation 2]
3. [Recommendation 3]

### Output for Next Stage
[Key information to pass forward]

### Stage Summary
[Brief summary of this stage's work]"""


def get_pipeline_summary_prompt(
    original_content: str,
    all_stage_outputs: str,
    stages_completed: list[str]
) -> str:
    """
    Generate a pipeline summary prompt.

    Args:
        original_content: Original input content
        all_stage_outputs: All stage outputs
        stages_completed: List of completed stage names

    Returns:
        Summary prompt string
    """
    stages_list = "\n".join(f"- {stage}" for stage in stages_completed)

    return f"""Synthesize the results from all pipeline stages into a comprehensive summary.

Original Content:
{original_content[:1000]}...

Stages Completed:
{stages_list}

All Stage Outputs:
{all_stage_outputs}

Please provide:

## Pipeline Summary

### Executive Summary
[2-3 sentence overview]

### Key Findings by Stage
{chr(10).join(f'#### {stage}{chr(10)}[Key findings]' for stage in stages_completed)}

### Critical Issues
| Priority | Stage | Issue | Status |
|----------|-------|-------|--------|
| [Critical/High/Medium] | [Stage] | [Issue] | [Open/Resolved] |

### Recommendations
1. [Prioritized recommendation]
2. [Prioritized recommendation]
3. [Prioritized recommendation]

### Overall Assessment
- Quality Score: [1-10]
- Completion Status: [Complete/Partial/Incomplete]
- Recommended Actions: [List]

### Final Summary
[Comprehensive conclusion]"""


class SequentialTemplate(BaseTemplate):
    """Template class for sequential pipeline prompts."""

    @staticmethod
    def get_stage_prompt(
        content: str,
        stage_name: str,
        stage_number: int,
        total_stages: int,
        previous_output: Optional[str] = None,
        focus: Optional[str] = None
    ) -> str:
        """Get the sequential stage prompt."""
        return get_sequential_stage_prompt(
            content, stage_name, stage_number, total_stages, previous_output, focus
        )

    @staticmethod
    def get_summary_prompt(
        original_content: str,
        all_stage_outputs: str,
        stages_completed: list[str]
    ) -> str:
        """Get the pipeline summary prompt."""
        return get_pipeline_summary_prompt(original_content, all_stage_outputs, stages_completed)
