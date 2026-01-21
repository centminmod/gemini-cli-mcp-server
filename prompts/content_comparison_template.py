"""
Content comparison templates.

This module provides templates for the gemini_content_comparison tool.
"""
from typing import Optional
from .base_template import BaseTemplate


def get_content_comparison_prompt(
    sources: str,
    comparison_type: str = "semantic",
    output_format: str = "structured",
    include_metrics: bool = True,
    focus_areas: Optional[str] = None
) -> str:
    """
    Generate a content comparison prompt.

    Args:
        sources: JSON array of sources to compare
        comparison_type: Type of comparison
        output_format: Output format
        include_metrics: Include similarity scores
        focus_areas: Focus areas for comparison

    Returns:
        Complete prompt string
    """
    comparison_instructions = {
        "semantic": """
Comparison Type: Semantic
- Compare meaning and intent
- Identify conceptual similarities/differences
- Consider context and interpretation""",
        "textual": """
Comparison Type: Textual
- Compare exact text content
- Identify additions, deletions, modifications
- Track character/word-level changes""",
        "structural": """
Comparison Type: Structural
- Compare organization and structure
- Identify hierarchy differences
- Analyze component relationships""",
        "factual": """
Comparison Type: Factual
- Compare factual claims
- Identify contradictions
- Verify consistency of information""",
        "code": """
Comparison Type: Code
- Compare code functionality
- Identify algorithmic differences
- Analyze API/interface changes"""
    }.get(comparison_type, "")

    format_instructions = {
        "structured": "Provide a structured analysis with clear sections",
        "matrix": "Provide a comparison matrix showing differences",
        "summary": "Provide a concise summary of key differences",
        "detailed": "Provide detailed line-by-line or section-by-section comparison",
        "json": "Return results as a JSON object"
    }.get(output_format, "")

    focus_section = ""
    if focus_areas:
        focus_section = f"\n\nFocus Areas: {focus_areas}"

    metrics_section = """
Include Metrics:
- Similarity percentage
- Difference count by category
- Confidence scores""" if include_metrics else ""

    return f"""Compare the following sources and analyze their similarities and differences.
{comparison_instructions}

Output Format: {format_instructions}
{metrics_section}{focus_section}

Sources to Compare:
{sources}

Please provide:

## 1. Overview
- Number of sources compared
- Brief description of each source
- Overall similarity assessment

## 2. Comparison Analysis

### Similarities
- Common elements
- Shared concepts
- Consistent information

### Differences
- Unique elements in each source
- Contradictions
- Variations in detail

## 3. Detailed Comparison

For each pair of sources:
| Aspect | Source 1 | Source 2 | Difference Type |
|--------|----------|----------|-----------------|
| [aspect] | [content] | [content] | [addition/removal/modification] |

## 4. Metrics (if requested)
- Overall similarity: [percentage]
- Semantic similarity: [percentage]
- Structural similarity: [percentage]

## 5. Key Findings
- Most significant differences
- Critical inconsistencies
- Notable patterns

## 6. Recommendations
- Which source to prefer (if applicable)
- How to reconcile differences
- Suggested improvements

## 7. Summary
Brief overall comparison summary"""


class ContentComparisonTemplate(BaseTemplate):
    """Template class for content comparison."""

    @staticmethod
    def get_prompt(
        sources: str,
        comparison_type: str = "semantic",
        output_format: str = "structured",
        include_metrics: bool = True,
        focus_areas: Optional[str] = None
    ) -> str:
        """Get the content comparison prompt."""
        return get_content_comparison_prompt(
            sources, comparison_type, output_format, include_metrics, focus_areas
        )
