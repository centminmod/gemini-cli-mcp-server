"""
Per-model rate limiting with O(1) operations.

This module provides rate limiting on a per-model basis with
memory-efficient deque-based algorithms.
"""
import logging
import time
from collections import deque
from typing import Optional
from dataclasses import dataclass

from modules.config.gemini_config import (
    GEMINI_RATE_LIMIT_REQUESTS,
    GEMINI_RATE_LIMIT_WINDOW,
)

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_window: int
    window_seconds: int
    burst_limit: Optional[int] = None


# Default rate limits by model
DEFAULT_RATE_LIMITS = {
    "gemini-2.5-pro": RateLimitConfig(
        requests_per_window=50,
        window_seconds=60,
        burst_limit=10
    ),
    "gemini-2.5-flash": RateLimitConfig(
        requests_per_window=100,
        window_seconds=60,
        burst_limit=20
    ),
    "gemini-1.5-pro": RateLimitConfig(
        requests_per_window=60,
        window_seconds=60,
        burst_limit=15
    ),
    "gemini-1.5-flash": RateLimitConfig(
        requests_per_window=120,
        window_seconds=60,
        burst_limit=25
    ),
    "default": RateLimitConfig(
        requests_per_window=GEMINI_RATE_LIMIT_REQUESTS,
        window_seconds=GEMINI_RATE_LIMIT_WINDOW,
        burst_limit=None
    ),
}


class PerModelRateLimiter:
    """Rate limiter with per-model tracking."""

    def __init__(self):
        self._windows: dict[str, deque] = {}
        self._configs: dict[str, RateLimitConfig] = dict(DEFAULT_RATE_LIMITS)
        self._stats = {
            "total_requests": 0,
            "allowed_requests": 0,
            "rejected_requests": 0,
            "by_model": {},
        }

    def _get_config(self, model: str) -> RateLimitConfig:
        """Get rate limit config for a model."""
        return self._configs.get(model, self._configs["default"])

    def _get_window(self, model: str) -> deque:
        """Get or create sliding window for a model."""
        if model not in self._windows:
            config = self._get_config(model)
            self._windows[model] = deque(maxlen=config.requests_per_window * 2)
        return self._windows[model]

    def _cleanup_window(self, window: deque, window_seconds: int):
        """Remove expired entries from window (O(k) where k = expired entries)."""
        cutoff = time.time() - window_seconds
        while window and window[0] < cutoff:
            window.popleft()

    def check_rate_limit(self, model: str) -> tuple[bool, dict]:
        """
        Check if a request is allowed under rate limits.

        Args:
            model: Model identifier

        Returns:
            Tuple of (allowed, info_dict)
        """
        self._stats["total_requests"] += 1

        config = self._get_config(model)
        window = self._get_window(model)
        current_time = time.time()

        # Cleanup expired entries
        self._cleanup_window(window, config.window_seconds)

        # Check if within limit
        if len(window) >= config.requests_per_window:
            self._stats["rejected_requests"] += 1
            self._track_model_stats(model, allowed=False)

            # Calculate retry time
            oldest = window[0] if window else current_time
            retry_after = max(0, config.window_seconds - (current_time - oldest))

            return False, {
                "allowed": False,
                "model": model,
                "current_count": len(window),
                "limit": config.requests_per_window,
                "window_seconds": config.window_seconds,
                "retry_after_seconds": retry_after,
                "reason": "rate_limit_exceeded"
            }

        # Check burst limit
        if config.burst_limit:
            recent_window = [t for t in window if current_time - t < 1.0]
            if len(recent_window) >= config.burst_limit:
                self._stats["rejected_requests"] += 1
                self._track_model_stats(model, allowed=False)

                return False, {
                    "allowed": False,
                    "model": model,
                    "current_burst": len(recent_window),
                    "burst_limit": config.burst_limit,
                    "retry_after_seconds": 1.0,
                    "reason": "burst_limit_exceeded"
                }

        # Allow request
        window.append(current_time)
        self._stats["allowed_requests"] += 1
        self._track_model_stats(model, allowed=True)

        return True, {
            "allowed": True,
            "model": model,
            "current_count": len(window),
            "limit": config.requests_per_window,
            "remaining": config.requests_per_window - len(window),
            "window_seconds": config.window_seconds,
        }

    def _track_model_stats(self, model: str, allowed: bool):
        """Track per-model statistics."""
        if model not in self._stats["by_model"]:
            self._stats["by_model"][model] = {
                "total": 0,
                "allowed": 0,
                "rejected": 0,
            }

        self._stats["by_model"][model]["total"] += 1
        if allowed:
            self._stats["by_model"][model]["allowed"] += 1
        else:
            self._stats["by_model"][model]["rejected"] += 1

    def set_rate_limit(
        self,
        model: str,
        requests_per_window: int,
        window_seconds: int = 60,
        burst_limit: Optional[int] = None
    ):
        """Set custom rate limit for a model."""
        self._configs[model] = RateLimitConfig(
            requests_per_window=requests_per_window,
            window_seconds=window_seconds,
            burst_limit=burst_limit
        )
        logger.info(f"Rate limit set for {model}: {requests_per_window} req/{window_seconds}s")

    def get_stats(self) -> dict:
        """Get rate limiting statistics."""
        return {
            **self._stats,
            "active_windows": len(self._windows),
            "configured_models": list(self._configs.keys()),
        }

    def reset(self):
        """Reset all rate limit windows."""
        self._windows.clear()
        logger.info("Rate limit windows reset")


# Global rate limiter instance
_limiter: Optional[PerModelRateLimiter] = None


def get_rate_limiter() -> PerModelRateLimiter:
    """Get or create the rate limiter instance."""
    global _limiter
    if _limiter is None:
        _limiter = PerModelRateLimiter()
    return _limiter


def check_rate_limit(model: str) -> tuple[bool, dict]:
    """Convenience function to check rate limit."""
    return get_rate_limiter().check_rate_limit(model)


def get_rate_limit_stats() -> dict:
    """Convenience function to get rate limit stats."""
    return get_rate_limiter().get_stats()
