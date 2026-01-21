"""
Validation collaboration templates.

This module provides templates for validation mode in gemini_ai_collaboration.
"""
from typing import Optional
from .base_template import BaseTemplate


def get_validation_prompt(
    content: str,
    validation_criteria: str,
    confidence_threshold: float = 0.7,
    context: Optional[str] = None
) -> str:
    """
    Generate a validation prompt.

    Args:
        content: Content to validate
        validation_criteria: Comma-separated validation criteria
        confidence_threshold: Minimum confidence required
        context: Additional context

    Returns:
        Validation prompt string
    """
    criteria_list = [c.strip() for c in validation_criteria.split(",")]
    criteria_section = "\n".join(f"- {criterion}" for criterion in criteria_list)

    context_section = ""
    if context:
        context_section = f"""

Context:
{context}
"""

    return f"""Validate the following content against the specified criteria.

Validation Criteria:
{criteria_section}

Confidence Threshold: {confidence_threshold} (report confidence for each criterion)
{context_section}

Content to Validate:
{content}

For each criterion, provide:

## Validation Results

### Criterion: [Name]
- **Status**: [Pass/Fail/Partial]
- **Confidence**: [0.0-1.0]
- **Evidence**: [Supporting evidence]
- **Issues**: [Any problems found]
- **Recommendations**: [If applicable]

---

[Repeat for each criterion]

---

## Summary

### Overall Validation Status
| Criterion | Status | Confidence |
|-----------|--------|------------|
| [criterion] | [Pass/Fail] | [0.0-1.0] |

### Aggregate Confidence: [average]

### Criteria Met: [count]/[total]

### Critical Failures
[List any criteria that failed with high importance]

### Recommendations
1. [Recommendation]
2. [Recommendation]

### Final Verdict
- **Overall Status**: [Valid/Invalid/Needs Review]
- **Confidence Level**: [High/Medium/Low]
- **Summary**: [Brief assessment]"""


def get_consensus_prompt(
    content: str,
    all_validations: str,
    validation_criteria: str,
    consensus_method: str = "weighted_majority",
    conflict_resolution: str = "detailed_analysis"
) -> str:
    """
    Generate a consensus-building prompt.

    Args:
        content: Original content
        all_validations: All validation results
        validation_criteria: Validation criteria used
        consensus_method: Method for reaching consensus
        conflict_resolution: How to resolve conflicts

    Returns:
        Consensus prompt string
    """
    method_instructions = {
        "simple_majority": "Use simple majority voting for each criterion",
        "weighted_majority": "Weight votes by confidence scores",
        "unanimous": "Require unanimous agreement for validation",
        "supermajority": "Require 2/3 majority for validation",
        "expert_panel": "Weight based on model expertise in relevant areas"
    }.get(consensus_method, "")

    conflict_instructions = {
        "ignore": "Skip conflicting results",
        "flag_only": "Flag conflicts without resolution",
        "detailed_analysis": "Provide detailed analysis of conflicts",
        "additional_validation": "Recommend additional validation for conflicts",
        "expert_arbitration": "Recommend expert review for conflicts"
    }.get(conflict_resolution, "")

    return f"""Build consensus from multiple validation results.

Consensus Method: {consensus_method}
{method_instructions}

Conflict Resolution: {conflict_resolution}
{conflict_instructions}

Validation Criteria:
{validation_criteria}

All Validation Results:
{all_validations}

Please provide:

## Consensus Analysis

### Per-Criterion Consensus

| Criterion | Consensus Status | Agreement Level | Confidence |
|-----------|------------------|-----------------|------------|
| [criterion] | [Pass/Fail/Conflict] | [%] | [0.0-1.0] |

### Agreement Summary
- Full Agreement: [count] criteria
- Majority Agreement: [count] criteria
- Conflict: [count] criteria

## Conflict Analysis

For each conflict:
### Criterion: [Name]
- **Disagreement**: [Description]
- **Perspectives**:
  - Model A: [View]
  - Model B: [View]
- **Analysis**: [Why they differ]
- **Resolution**: [Recommended resolution]

## Confidence Aggregation
- Method: {consensus_method}
- Overall Confidence: [calculated value]
- Reliability: [High/Medium/Low]

## Final Consensus

### Validation Result
- **Status**: [Valid/Invalid/Inconclusive]
- **Confidence**: [0.0-1.0]
- **Criteria Met**: [count]/[total]

### Key Findings
1. [Finding]
2. [Finding]
3. [Finding]

### Recommendations
1. [Action item]
2. [Action item]

### Summary
[Final consensus statement]"""


class ValidationTemplate(BaseTemplate):
    """Template class for validation prompts."""

    @staticmethod
    def get_validation_prompt(
        content: str,
        validation_criteria: str,
        confidence_threshold: float = 0.7,
        context: Optional[str] = None
    ) -> str:
        """Get the validation prompt."""
        return get_validation_prompt(content, validation_criteria, confidence_threshold, context)

    @staticmethod
    def get_consensus_prompt(
        content: str,
        all_validations: str,
        validation_criteria: str,
        consensus_method: str = "weighted_majority",
        conflict_resolution: str = "detailed_analysis"
    ) -> str:
        """Get the consensus prompt."""
        return get_consensus_prompt(
            content, all_validations, validation_criteria, consensus_method, conflict_resolution
        )
