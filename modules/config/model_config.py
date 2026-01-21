"""
Model definitions and configuration for Gemini CLI MCP Server.

This module defines available models and their capabilities.
"""

# Gemini Models with capabilities
GEMINI_MODELS = {
    "gemini-2.5-pro": {
        "description": "Most capable model for complex tasks",
        "context_window": "1M tokens",
        "context_tokens": 1000000,
        "scaling_factor": 1.0,
        "best_for": ["complex analysis", "code review", "creative tasks", "long context"],
        "pricing_tier": "premium",
        "supports_sandbox": True,
        "supports_vision": True,
    },
    "gemini-2.5-flash": {
        "description": "Fast, efficient model for most tasks",
        "context_window": "1M tokens",
        "context_tokens": 1000000,
        "scaling_factor": 1.0,
        "best_for": ["quick responses", "simple tasks", "high throughput", "cost efficiency"],
        "pricing_tier": "standard",
        "supports_sandbox": True,
        "supports_vision": True,
    },
    "gemini-1.5-pro": {
        "description": "Stable production model",
        "context_window": "128K tokens",
        "context_tokens": 128000,
        "scaling_factor": 0.8,
        "best_for": ["production workloads", "reliability", "stable behavior"],
        "pricing_tier": "standard",
        "supports_sandbox": True,
        "supports_vision": True,
    },
    "gemini-1.5-flash": {
        "description": "Fast model for simpler tasks",
        "context_window": "128K tokens",
        "context_tokens": 128000,
        "scaling_factor": 0.6,
        "best_for": ["speed-critical tasks", "simple queries", "cost optimization"],
        "pricing_tier": "economy",
        "supports_sandbox": True,
        "supports_vision": True,
    },
    "gemini-1.0-pro": {
        "description": "Legacy model for compatibility",
        "context_window": "32K tokens",
        "context_tokens": 32000,
        "scaling_factor": 0.4,
        "best_for": ["legacy compatibility", "simple tasks"],
        "pricing_tier": "economy",
        "supports_sandbox": False,
        "supports_vision": False,
    },
}

# Model fallback chain
MODEL_FALLBACK_CHAIN = {
    "gemini-2.5-pro": "gemini-2.5-flash",
    "gemini-2.5-flash": "gemini-1.5-flash",
    "gemini-1.5-pro": "gemini-1.5-flash",
    "gemini-1.5-flash": "gemini-1.0-pro",
    "gemini-1.0-pro": None,
}

# Default models for different task types
DEFAULT_MODELS_BY_TASK = {
    "complex_analysis": "gemini-2.5-pro",
    "code_review": "gemini-2.5-pro",
    "quick_response": "gemini-2.5-flash",
    "summarization": "gemini-2.5-flash",
    "sandbox_execution": "gemini-2.5-pro",
    "conversation": "gemini-2.5-flash",
    "collaboration": "gemini-2.5-flash",
}


def get_model_info(model: str) -> dict:
    """Get information about a specific model."""
    return GEMINI_MODELS.get(model, {
        "description": "Unknown model",
        "context_window": "Unknown",
        "scaling_factor": 1.0,
    })


def get_scaling_factor(model: str) -> float:
    """Get the scaling factor for a model."""
    model_info = GEMINI_MODELS.get(model, {})
    return model_info.get("scaling_factor", 1.0)


def get_fallback_model(model: str) -> str | None:
    """Get the fallback model for a given model."""
    return MODEL_FALLBACK_CHAIN.get(model)


def get_model_for_task(task_type: str) -> str:
    """Get the recommended model for a task type."""
    return DEFAULT_MODELS_BY_TASK.get(task_type, "gemini-2.5-flash")


def supports_feature(model: str, feature: str) -> bool:
    """Check if a model supports a specific feature."""
    model_info = GEMINI_MODELS.get(model, {})
    feature_key = f"supports_{feature}"
    return model_info.get(feature_key, False)
