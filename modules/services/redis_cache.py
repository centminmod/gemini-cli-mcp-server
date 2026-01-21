"""
Redis caching with graceful memory fallback.

This module provides Redis caching functionality with automatic
fallback to in-memory caching when Redis is unavailable.
"""
import json
import logging
import time
from typing import Optional, Any

from modules.config.gemini_config import (
    GEMINI_REDIS_HOST,
    GEMINI_REDIS_PORT,
    GEMINI_REDIS_DB,
)

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache with memory fallback."""

    def __init__(
        self,
        host: str = GEMINI_REDIS_HOST,
        port: int = GEMINI_REDIS_PORT,
        db: int = GEMINI_REDIS_DB,
        prefix: str = "gemini:",
        default_ttl: int = 3600
    ):
        """
        Initialize Redis cache.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database
            prefix: Key prefix
            default_ttl: Default TTL in seconds
        """
        self.host = host
        self.port = port
        self.db = db
        self.prefix = prefix
        self.default_ttl = default_ttl

        self._client = None
        self._memory_cache: dict[str, tuple[Any, float]] = {}
        self._use_memory_fallback = False

        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0,
        }

        self._connect()

    def _connect(self):
        """Connect to Redis."""
        try:
            import redis
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,
                socket_timeout=5.0
            )
            # Test connection
            self._client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
            self._use_memory_fallback = False
        except ImportError:
            logger.warning("redis package not installed, using memory fallback")
            self._client = None
            self._use_memory_fallback = True
        except Exception as e:
            logger.warning(f"Redis connection failed ({e}), using memory fallback")
            self._client = None
            self._use_memory_fallback = True

    def _key(self, key: str) -> str:
        """Generate prefixed key."""
        return f"{self.prefix}{key}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        full_key = self._key(key)

        if self._use_memory_fallback:
            return self._memory_get(full_key)

        try:
            value = self._client.get(full_key)
            if value:
                self._stats["hits"] += 1
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            else:
                self._stats["misses"] += 1
                return None
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Redis get error: {e}")
            return self._memory_get(full_key)

    def _memory_get(self, key: str) -> Optional[Any]:
        """Get from memory cache."""
        if key in self._memory_cache:
            value, expiry = self._memory_cache[key]
            if expiry == 0 or time.time() < expiry:
                self._stats["hits"] += 1
                return value
            else:
                del self._memory_cache[key]

        self._stats["misses"] += 1
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (None = default)

        Returns:
            True if successful
        """
        full_key = self._key(key)
        ttl = ttl or self.default_ttl

        if self._use_memory_fallback:
            return self._memory_set(full_key, value, ttl)

        try:
            serialized = json.dumps(value) if not isinstance(value, str) else value
            self._client.setex(full_key, ttl, serialized)
            self._stats["sets"] += 1
            return True
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Redis set error: {e}")
            return self._memory_set(full_key, value, ttl)

    def _memory_set(self, key: str, value: Any, ttl: int) -> bool:
        """Set in memory cache."""
        expiry = time.time() + ttl if ttl > 0 else 0
        self._memory_cache[key] = (value, expiry)
        self._stats["sets"] += 1

        # Limit memory cache size
        if len(self._memory_cache) > 10000:
            self._cleanup_memory_cache()

        return True

    def _cleanup_memory_cache(self):
        """Clean up expired entries from memory cache."""
        current_time = time.time()
        expired = [
            k for k, (_, expiry) in self._memory_cache.items()
            if expiry > 0 and current_time > expiry
        ]
        for k in expired:
            del self._memory_cache[k]

        # If still too big, remove oldest entries
        if len(self._memory_cache) > 8000:
            # Simple approach: remove half
            keys_to_remove = list(self._memory_cache.keys())[:len(self._memory_cache) // 2]
            for k in keys_to_remove:
                del self._memory_cache[k]

    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted
        """
        full_key = self._key(key)

        if self._use_memory_fallback:
            if full_key in self._memory_cache:
                del self._memory_cache[full_key]
                self._stats["deletes"] += 1
                return True
            return False

        try:
            result = self._client.delete(full_key)
            if result:
                self._stats["deletes"] += 1
            return bool(result)
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Redis delete error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        full_key = self._key(key)

        if self._use_memory_fallback:
            if full_key in self._memory_cache:
                _, expiry = self._memory_cache[full_key]
                return expiry == 0 or time.time() < expiry
            return False

        try:
            return bool(self._client.exists(full_key))
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Redis exists error: {e}")
            return False

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total_ops = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_ops * 100 if total_ops > 0 else 0

        return {
            **self._stats,
            "hit_rate_percent": hit_rate,
            "backend": "redis" if not self._use_memory_fallback else "memory",
            "memory_cache_size": len(self._memory_cache) if self._use_memory_fallback else 0,
        }


# Global cache instance
_cache: Optional[RedisCache] = None


def get_redis_cache() -> RedisCache:
    """Get or create the Redis cache instance."""
    global _cache
    if _cache is None:
        _cache = RedisCache()
    return _cache


def get_redis_client():
    """Get the raw Redis client (for direct operations)."""
    cache = get_redis_cache()
    if cache._client:
        return cache._client
    return None


def get_redis_stats() -> dict:
    """Get Redis cache statistics."""
    return get_redis_cache().get_stats()


# Convenience functions
def cache_get(key: str) -> Optional[Any]:
    """Get from cache."""
    return get_redis_cache().get(key)


def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set in cache."""
    return get_redis_cache().set(key, value, ttl)


def cache_delete(key: str) -> bool:
    """Delete from cache."""
    return get_redis_cache().delete(key)
