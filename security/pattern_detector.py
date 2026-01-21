"""
Security pattern detection for threat prevention.

This module detects potential security threats including:
- Command injection
- Path traversal
- XSS attacks
- SQL injection
- Prompt injection
"""
import re
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SecurityThreat:
    """Represents a detected security threat."""
    threat_type: str
    severity: str  # critical, high, medium, low
    pattern_matched: str
    location: int
    description: str


# Security threat patterns
THREAT_PATTERNS = {
    "command_injection": {
        "severity": "critical",
        "patterns": [
            r';\s*(rm|del|format|mkfs|dd)\s',
            r'\|\s*(cat|nc|curl|wget)\s',
            r'`[^`]*`',
            r'\$\([^)]*\)',
            r'&&\s*(rm|del|shutdown|reboot)',
            r'\|\|\s*(rm|del|shutdown|reboot)',
        ],
        "description": "Potential command injection attempt"
    },
    "path_traversal": {
        "severity": "high",
        "patterns": [
            r'\.\./\.\.',
            r'\.\.\\\\',
            r'%2e%2e%2f',
            r'%2e%2e/',
            r'/etc/passwd',
            r'/etc/shadow',
            r'C:\\Windows\\System32',
        ],
        "description": "Potential path traversal attempt"
    },
    "xss": {
        "severity": "high",
        "patterns": [
            r'<script[^>]*>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
        ],
        "description": "Potential XSS attack"
    },
    "sql_injection": {
        "severity": "high",
        "patterns": [
            r"'\s*(or|and)\s+'",
            r'"\s*(or|and)\s+"',
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into.*values',
            r';\s*--',
        ],
        "description": "Potential SQL injection attempt"
    },
    "prompt_injection": {
        "severity": "medium",
        "patterns": [
            r'ignore\s+(previous|all)\s+(instructions|prompts)',
            r'disregard\s+(previous|all)\s+(instructions|prompts)',
            r'forget\s+(previous|all)\s+(instructions|prompts)',
            r'you\s+are\s+now\s+a\s+',
            r'pretend\s+you\s+are\s+',
            r'act\s+as\s+if\s+you\s+',
        ],
        "description": "Potential prompt injection attempt"
    },
    "information_disclosure": {
        "severity": "medium",
        "patterns": [
            r'show\s+(all\s+)?environment',
            r'print\s+env',
            r'echo\s+\$\w+',
            r'printenv',
            r'env\s*$',
        ],
        "description": "Potential information disclosure attempt"
    }
}

# Compile patterns
COMPILED_THREAT_PATTERNS = {}
for threat_type, config in THREAT_PATTERNS.items():
    COMPILED_THREAT_PATTERNS[threat_type] = {
        "severity": config["severity"],
        "patterns": [re.compile(p, re.IGNORECASE) for p in config["patterns"]],
        "description": config["description"]
    }


class PatternDetector:
    """Detects security threat patterns in content."""

    def __init__(self, enabled_threats: Optional[list[str]] = None):
        """
        Initialize detector with optional threat filtering.

        Args:
            enabled_threats: List of threat types to detect (None = all)
        """
        self.enabled_threats = enabled_threats or list(COMPILED_THREAT_PATTERNS.keys())

    def detect(self, content: str) -> list[SecurityThreat]:
        """
        Detect security threats in content.

        Args:
            content: Text content to analyze

        Returns:
            List of detected threats
        """
        if not content:
            return []

        threats = []

        for threat_type in self.enabled_threats:
            if threat_type not in COMPILED_THREAT_PATTERNS:
                continue

            config = COMPILED_THREAT_PATTERNS[threat_type]

            for pattern in config["patterns"]:
                for match in pattern.finditer(content):
                    threats.append(SecurityThreat(
                        threat_type=threat_type,
                        severity=config["severity"],
                        pattern_matched=match.group(),
                        location=match.start(),
                        description=config["description"]
                    ))

        return sorted(threats, key=lambda t: t.location)

    def is_safe(self, content: str) -> bool:
        """
        Check if content is safe (no threats detected).

        Args:
            content: Text content to check

        Returns:
            True if safe, False if threats detected
        """
        return len(self.detect(content)) == 0

    def get_threat_summary(self, content: str) -> dict:
        """
        Get a summary of threats in content.

        Args:
            content: Text content to analyze

        Returns:
            Summary dictionary
        """
        threats = self.detect(content)

        if not threats:
            return {"safe": True, "threat_count": 0}

        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        by_type = {}

        for threat in threats:
            by_severity[threat.severity] = by_severity.get(threat.severity, 0) + 1
            by_type[threat.threat_type] = by_type.get(threat.threat_type, 0) + 1

        return {
            "safe": False,
            "threat_count": len(threats),
            "by_severity": by_severity,
            "by_type": by_type,
            "highest_severity": (
                "critical" if by_severity["critical"] > 0 else
                "high" if by_severity["high"] > 0 else
                "medium" if by_severity["medium"] > 0 else
                "low"
            )
        }


# Global detector instance
_detector = PatternDetector()


def detect_security_threats(content: str) -> list[SecurityThreat]:
    """
    Convenience function to detect threats in content.

    Args:
        content: Text content to analyze

    Returns:
        List of detected threats
    """
    return _detector.detect(content)


def is_content_safe(content: str) -> bool:
    """
    Check if content is safe.

    Args:
        content: Text content to check

    Returns:
        True if safe
    """
    return _detector.is_safe(content)
