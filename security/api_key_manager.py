"""
API key management with secure storage and rotation.

This module provides secure API key management functionality.
"""
import os
import hashlib
import logging
import time
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class APIKeyInfo:
    """Information about an API key."""
    key_hash: str
    name: str
    created_at: float
    last_used: float
    usage_count: int
    is_active: bool


class APIKeyManager:
    """Manages API keys securely."""

    def __init__(self):
        self._keys: dict[str, APIKeyInfo] = {}
        self._usage_tracking: dict[str, int] = {}

    def _hash_key(self, key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(key.encode()).hexdigest()

    def register_key(self, key: str, name: str) -> bool:
        """Register an API key."""
        key_hash = self._hash_key(key)
        if key_hash in self._keys:
            return False

        self._keys[key_hash] = APIKeyInfo(
            key_hash=key_hash,
            name=name,
            created_at=time.time(),
            last_used=0,
            usage_count=0,
            is_active=True
        )
        return True

    def validate_key(self, key: str) -> bool:
        """Validate an API key."""
        key_hash = self._hash_key(key)
        key_info = self._keys.get(key_hash)

        if not key_info:
            return False

        if not key_info.is_active:
            return False

        # Update usage
        key_info.last_used = time.time()
        key_info.usage_count += 1

        return True

    def revoke_key(self, key: str) -> bool:
        """Revoke an API key."""
        key_hash = self._hash_key(key)
        key_info = self._keys.get(key_hash)

        if not key_info:
            return False

        key_info.is_active = False
        logger.info(f"API key {key_info.name} revoked")
        return True

    def get_key_info(self, key: str) -> Optional[dict]:
        """Get information about an API key."""
        key_hash = self._hash_key(key)
        key_info = self._keys.get(key_hash)

        if not key_info:
            return None

        return {
            "name": key_info.name,
            "created_at": key_info.created_at,
            "last_used": key_info.last_used,
            "usage_count": key_info.usage_count,
            "is_active": key_info.is_active
        }

    def list_keys(self) -> list[dict]:
        """List all registered keys (without actual keys)."""
        return [
            {
                "name": info.name,
                "created_at": info.created_at,
                "last_used": info.last_used,
                "usage_count": info.usage_count,
                "is_active": info.is_active
            }
            for info in self._keys.values()
        ]


def get_api_key_from_env(key_name: str) -> Optional[str]:
    """Safely get an API key from environment variables."""
    key = os.getenv(key_name)
    if key:
        # Log that key was found (but not the key itself)
        logger.debug(f"API key {key_name} found in environment")
    return key


def mask_api_key(key: str, visible_chars: int = 4) -> str:
    """Mask an API key for display."""
    if len(key) <= visible_chars * 2:
        return "*" * len(key)
    return key[:visible_chars] + "*" * (len(key) - visible_chars * 2) + key[-visible_chars:]
