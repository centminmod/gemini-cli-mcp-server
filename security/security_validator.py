"""
Input validation for security.

This module provides validation functions for user inputs.
"""
import re
import logging
from typing import Optional, Tuple

from .pattern_detector import PatternDetector, SecurityThreat
from .credential_sanitizer import check_for_credentials

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Validates inputs for security issues."""

    def __init__(
        self,
        max_input_length: int = 1000000,
        allow_file_paths: bool = True,
        allow_urls: bool = True,
        strict_mode: bool = False
    ):
        """
        Initialize validator.

        Args:
            max_input_length: Maximum allowed input length
            allow_file_paths: Allow file path syntax (@filename)
            allow_urls: Allow URLs in input
            strict_mode: Enable strict validation
        """
        self.max_input_length = max_input_length
        self.allow_file_paths = allow_file_paths
        self.allow_urls = allow_urls
        self.strict_mode = strict_mode
        self._detector = PatternDetector()

    def validate(self, content: str) -> Tuple[bool, list[str]]:
        """
        Validate content for security issues.

        Args:
            content: Content to validate

        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []

        # Check length
        if len(content) > self.max_input_length:
            issues.append(f"Input exceeds maximum length of {self.max_input_length}")

        # Check for threats
        threats = self._detector.detect(content)
        critical_threats = [t for t in threats if t.severity in ("critical", "high")]

        if critical_threats:
            for threat in critical_threats:
                issues.append(f"{threat.description}: {threat.pattern_matched[:50]}")

        # Check for embedded credentials (should not be in user input)
        if check_for_credentials(content):
            issues.append("Input appears to contain credentials - please remove them")

        # Strict mode checks
        if self.strict_mode:
            # Check for potentially dangerous patterns
            if re.search(r'eval\s*\(', content):
                issues.append("eval() detected - potentially dangerous")
            if re.search(r'exec\s*\(', content):
                issues.append("exec() detected - potentially dangerous")

        is_valid = len(issues) == 0
        return is_valid, issues

    def sanitize_for_logging(self, content: str) -> str:
        """
        Sanitize content for safe logging.

        Args:
            content: Content to sanitize

        Returns:
            Sanitized content
        """
        from .credential_sanitizer import sanitize_credentials

        # Truncate if too long
        if len(content) > 1000:
            content = content[:1000] + "...[truncated]"

        # Remove credentials
        content = sanitize_credentials(content)

        return content

    def get_validation_report(self, content: str) -> dict:
        """
        Get a detailed validation report.

        Args:
            content: Content to validate

        Returns:
            Validation report dictionary
        """
        is_valid, issues = self.validate(content)
        threats = self._detector.detect(content)

        return {
            "is_valid": is_valid,
            "issues": issues,
            "content_length": len(content),
            "threat_count": len(threats),
            "threats": [
                {
                    "type": t.threat_type,
                    "severity": t.severity,
                    "description": t.description
                }
                for t in threats
            ],
            "contains_credentials": check_for_credentials(content),
        }


# Global validator instance
_validator = SecurityValidator()


def validate_input(content: str) -> Tuple[bool, list[str]]:
    """
    Convenience function to validate input.

    Args:
        content: Content to validate

    Returns:
        Tuple of (is_valid, list of issues)
    """
    return _validator.validate(content)


def is_input_safe(content: str) -> bool:
    """
    Check if input is safe.

    Args:
        content: Content to check

    Returns:
        True if safe
    """
    is_valid, _ = _validator.validate(content)
    return is_valid
