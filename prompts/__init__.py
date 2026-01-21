"""
Template module for Gemini CLI MCP Server.

This module provides prompt templates for all analysis tools with TTL caching.
"""
from .template_loader import TemplateLoader, get_template
from .base_template import BaseTemplate
from .summarize_template import get_summarize_prompt
from .eval_template import get_eval_plan_prompt
from .review_template import get_review_code_prompt
from .verify_template import get_verify_solution_prompt

__all__ = [
    "TemplateLoader",
    "get_template",
    "BaseTemplate",
    "get_summarize_prompt",
    "get_eval_plan_prompt",
    "get_review_code_prompt",
    "get_verify_solution_prompt",
]
