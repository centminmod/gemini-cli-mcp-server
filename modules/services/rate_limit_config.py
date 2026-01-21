"""
Rate limit configuration and management.

This module provides configuration options for rate limiting.
"""
import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class ModelRateLimitConfig:
    """Rate limit configuration for a specific model."""
    model: str
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_limit: int
    priority: int  # Higher = more priority


# Environment-based configuration
DEFAULT_REQUESTS_PER_MINUTE = int(os.getenv("GEMINI_RATE_LIMIT_REQUESTS", "100"))
DEFAULT_WINDOW_SECONDS = int(os.getenv("GEMINI_RATE_LIMIT_WINDOW", "60"))

# Model-specific rate limits
MODEL_RATE_LIMITS = {
    "gemini-2.5-pro": ModelRateLimitConfig(
        model="gemini-2.5-pro",
        requests_per_minute=50,
        requests_per_hour=500,
        requests_per_day=5000,
        burst_limit=10,
        priority=10
    ),
    "gemini-2.5-flash": ModelRateLimitConfig(
        model="gemini-2.5-flash",
        requests_per_minute=100,
        requests_per_hour=1000,
        requests_per_day=10000,
        burst_limit=20,
        priority=8
    ),
    "gemini-1.5-pro": ModelRateLimitConfig(
        model="gemini-1.5-pro",
        requests_per_minute=60,
        requests_per_hour=600,
        requests_per_day=6000,
        burst_limit=15,
        priority=7
    ),
    "gemini-1.5-flash": ModelRateLimitConfig(
        model="gemini-1.5-flash",
        requests_per_minute=120,
        requests_per_hour=1200,
        requests_per_day=12000,
        burst_limit=25,
        priority=5
    ),
}


def get_model_rate_limit(model: str) -> ModelRateLimitConfig:
    """Get rate limit configuration for a model."""
    if model in MODEL_RATE_LIMITS:
        return MODEL_RATE_LIMITS[model]

    # Return default config for unknown models
    return ModelRateLimitConfig(
        model=model,
        requests_per_minute=DEFAULT_REQUESTS_PER_MINUTE,
        requests_per_hour=DEFAULT_REQUESTS_PER_MINUTE * 10,
        requests_per_day=DEFAULT_REQUESTS_PER_MINUTE * 100,
        burst_limit=DEFAULT_REQUESTS_PER_MINUTE // 5,
        priority=1
    )


def get_all_rate_limits() -> dict[str, ModelRateLimitConfig]:
    """Get all configured rate limits."""
    return dict(MODEL_RATE_LIMITS)


def set_model_rate_limit(
    model: str,
    requests_per_minute: Optional[int] = None,
    requests_per_hour: Optional[int] = None,
    requests_per_day: Optional[int] = None,
    burst_limit: Optional[int] = None,
    priority: Optional[int] = None
):
    """
    Set or update rate limit for a model.

    Args:
        model: Model identifier
        requests_per_minute: Max requests per minute
        requests_per_hour: Max requests per hour
        requests_per_day: Max requests per day
        burst_limit: Max burst requests
        priority: Priority level
    """
    existing = MODEL_RATE_LIMITS.get(model)

    MODEL_RATE_LIMITS[model] = ModelRateLimitConfig(
        model=model,
        requests_per_minute=requests_per_minute or (existing.requests_per_minute if existing else 100),
        requests_per_hour=requests_per_hour or (existing.requests_per_hour if existing else 1000),
        requests_per_day=requests_per_day or (existing.requests_per_day if existing else 10000),
        burst_limit=burst_limit or (existing.burst_limit if existing else 20),
        priority=priority or (existing.priority if existing else 1)
    )
