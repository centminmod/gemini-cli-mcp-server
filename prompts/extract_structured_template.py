"""
Structured data extraction templates.

This module provides templates for the gemini_extract_structured tool.
"""
from typing import Optional
from .base_template import BaseTemplate


def get_extract_structured_prompt(
    content: str,
    schema: str,
    examples: Optional[str] = None,
    strict_mode: bool = True
) -> str:
    """
    Generate a structured data extraction prompt.

    Args:
        content: Content to extract from
        schema: JSON schema for output
        examples: Optional examples
        strict_mode: Whether to enforce strict schema compliance

    Returns:
        Complete prompt string
    """
    strict_text = """
IMPORTANT: You MUST strictly follow the provided schema.
- All required fields must be present
- Field types must match exactly
- No additional fields unless specified
""" if strict_mode else """
Note: Follow the schema as closely as possible, but you may include
additional relevant information if it adds value.
"""

    examples_section = ""
    if examples:
        examples_section = f"""

Examples of Expected Output:
{examples}
"""

    return f"""Extract structured data from the following content according to the provided JSON schema.
{strict_text}

JSON Schema:
```json
{schema}
```
{examples_section}

Content to Analyze:
{content}

Instructions:
1. Carefully analyze the content
2. Extract information matching the schema structure
3. Ensure all data types match the schema
4. Handle missing data appropriately (null or omit based on schema)
5. Return ONLY valid JSON that conforms to the schema

Output your response as a valid JSON object:"""


class ExtractStructuredTemplate(BaseTemplate):
    """Template class for structured data extraction."""

    @staticmethod
    def get_prompt(
        content: str,
        schema: str,
        examples: Optional[str] = None,
        strict_mode: bool = True
    ) -> str:
        """Get the structured extraction prompt."""
        return get_extract_structured_prompt(content, schema, examples, strict_mode)
