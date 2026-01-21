"""
Template loading with TTL caching and integrity verification.

This module provides template loading functionality with 30-minute TTL caching
and SHA-256 integrity verification.
"""
import hashlib
import logging
from typing import Optional, Callable
from cachetools import TTLCache

logger = logging.getLogger(__name__)

# Template cache with 30-minute TTL
TEMPLATE_CACHE: TTLCache = TTLCache(maxsize=50, ttl=1800)


class TemplateLoader:
    """Template loader with caching and integrity verification."""

    def __init__(self):
        self.cache = TEMPLATE_CACHE
        self._integrity_hashes = {}

    def get_template(
        self,
        template_name: str,
        template_func: Callable[..., str],
        *args,
        **kwargs
    ) -> str:
        """
        Get a template with caching.

        Args:
            template_name: Name of the template for caching
            template_func: Function that generates the template
            *args: Positional arguments for template_func
            **kwargs: Keyword arguments for template_func

        Returns:
            Generated template string
        """
        # Create cache key from template name and arguments
        cache_key = self._create_cache_key(template_name, args, kwargs)

        if cache_key in self.cache:
            logger.debug(f"Template cache hit: {template_name}")
            return self.cache[cache_key]

        logger.debug(f"Template cache miss: {template_name}")
        template = template_func(*args, **kwargs)

        # Store in cache
        self.cache[cache_key] = template

        # Compute and store integrity hash
        self._integrity_hashes[cache_key] = self._compute_hash(template)

        return template

    def _create_cache_key(self, name: str, args: tuple, kwargs: dict) -> str:
        """Create a cache key from template name and arguments."""
        key_parts = [name]

        for arg in args:
            if isinstance(arg, str):
                key_parts.append(arg[:100])  # Truncate long strings
            else:
                key_parts.append(str(arg))

        for k, v in sorted(kwargs.items()):
            if isinstance(v, str):
                key_parts.append(f"{k}:{v[:50]}")
            else:
                key_parts.append(f"{k}:{v}")

        return "|".join(key_parts)

    def _compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def verify_integrity(self, template_name: str, content: str) -> bool:
        """Verify template integrity against stored hash."""
        cache_key = template_name
        if cache_key not in self._integrity_hashes:
            return True  # No stored hash to verify against

        expected_hash = self._integrity_hashes[cache_key]
        actual_hash = self._compute_hash(content)
        return expected_hash == actual_hash

    def clear_cache(self):
        """Clear the template cache."""
        self.cache.clear()
        self._integrity_hashes.clear()
        logger.info("Template cache cleared")

    def get_stats(self) -> dict:
        """Get template cache statistics."""
        return {
            "cache_size": len(self.cache),
            "cache_maxsize": self.cache.maxsize,
            "cache_ttl": self.cache.ttl,
            "integrity_hashes_count": len(self._integrity_hashes),
        }


# Global template loader instance
_loader = TemplateLoader()


def get_template(
    template_name: str,
    template_func: Callable[..., str],
    *args,
    **kwargs
) -> str:
    """
    Convenience function to get a cached template.

    Args:
        template_name: Name of the template
        template_func: Function that generates the template
        *args: Arguments for the template function
        **kwargs: Keyword arguments for the template function

    Returns:
        Generated template string
    """
    return _loader.get_template(template_name, template_func, *args, **kwargs)


def get_template_stats() -> dict:
    """Get template loader statistics."""
    return _loader.get_stats()


def clear_template_cache():
    """Clear the global template cache."""
    _loader.clear_cache()
