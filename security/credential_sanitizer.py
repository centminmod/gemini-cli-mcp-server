"""
Credential sanitization for secure output handling.

This module provides functions to remove or mask sensitive information
from outputs before logging or returning to clients.
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Patterns for detecting credentials
CREDENTIAL_PATTERNS = [
    # API Keys
    (r'AIza[0-9A-Za-z_-]{35}', '[REDACTED_GOOGLE_API_KEY]'),
    (r'sk-[a-zA-Z0-9]{32,}', '[REDACTED_OPENAI_KEY]'),
    (r'sk-or-v1-[a-zA-Z0-9]{64}', '[REDACTED_OPENROUTER_KEY]'),
    (r'sk-ant-[a-zA-Z0-9-]{40,}', '[REDACTED_ANTHROPIC_KEY]'),

    # AWS
    (r'AKIA[0-9A-Z]{16}', '[REDACTED_AWS_ACCESS_KEY]'),
    (r'(?<![A-Za-z0-9/+])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])', '[REDACTED_AWS_SECRET]'),

    # Bearer tokens
    (r'Bearer\s+[a-zA-Z0-9._-]+', 'Bearer [REDACTED]'),

    # Generic secrets
    (r'password["\s]*[:=]["\s]*[^\s"]+', 'password=[REDACTED]'),
    (r'secret["\s]*[:=]["\s]*[^\s"]+', 'secret=[REDACTED]'),
    (r'token["\s]*[:=]["\s]*[^\s"]+', 'token=[REDACTED]'),
    (r'api[_-]?key["\s]*[:=]["\s]*[^\s"]+', 'api_key=[REDACTED]'),

    # Private keys
    (r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----[\s\S]*?-----END (RSA |EC |DSA )?PRIVATE KEY-----',
     '[REDACTED_PRIVATE_KEY]'),

    # JWT tokens
    (r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*', '[REDACTED_JWT]'),
]

# Compile patterns for performance
COMPILED_PATTERNS = [
    (re.compile(pattern, re.IGNORECASE), replacement)
    for pattern, replacement in CREDENTIAL_PATTERNS
]


class CredentialSanitizer:
    """Sanitizes credentials from text content."""

    def __init__(self, additional_patterns: Optional[list] = None):
        """
        Initialize sanitizer with optional additional patterns.

        Args:
            additional_patterns: List of (pattern, replacement) tuples
        """
        self.patterns = list(COMPILED_PATTERNS)

        if additional_patterns:
            for pattern, replacement in additional_patterns:
                self.patterns.append(
                    (re.compile(pattern, re.IGNORECASE), replacement)
                )

    def sanitize(self, content: str) -> str:
        """
        Sanitize content by removing/masking credentials.

        Args:
            content: Text content to sanitize

        Returns:
            Sanitized content
        """
        if not content:
            return content

        result = content
        for pattern, replacement in self.patterns:
            result = pattern.sub(replacement, result)

        return result

    def contains_credentials(self, content: str) -> bool:
        """
        Check if content contains potential credentials.

        Args:
            content: Text content to check

        Returns:
            True if credentials detected
        """
        if not content:
            return False

        for pattern, _ in self.patterns:
            if pattern.search(content):
                return True

        return False

    def get_credential_locations(self, content: str) -> list[dict]:
        """
        Find locations of credentials in content.

        Args:
            content: Text content to search

        Returns:
            List of credential location info
        """
        if not content:
            return []

        locations = []
        for pattern, replacement in self.patterns:
            for match in pattern.finditer(content):
                locations.append({
                    "start": match.start(),
                    "end": match.end(),
                    "type": replacement.strip("[]"),
                    "masked": replacement
                })

        return sorted(locations, key=lambda x: x["start"])


# Global sanitizer instance
_sanitizer = CredentialSanitizer()


def sanitize_credentials(content: str) -> str:
    """
    Convenience function to sanitize credentials from content.

    Args:
        content: Text content to sanitize

    Returns:
        Sanitized content
    """
    return _sanitizer.sanitize(content)


def check_for_credentials(content: str) -> bool:
    """
    Check if content contains credentials.

    Args:
        content: Text content to check

    Returns:
        True if credentials found
    """
    return _sanitizer.contains_credentials(content)
