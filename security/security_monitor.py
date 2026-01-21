"""
Security monitoring and alerting.

This module provides real-time security monitoring capabilities.
"""
import logging
import time
from typing import Optional, Callable
from collections import deque
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SecurityEvent:
    """Represents a security event."""
    event_type: str
    severity: str
    timestamp: float
    source: str
    details: dict
    handled: bool = False


class SecurityMonitor:
    """Monitors security events and provides alerting."""

    def __init__(
        self,
        max_events: int = 1000,
        alert_callback: Optional[Callable] = None
    ):
        """
        Initialize security monitor.

        Args:
            max_events: Maximum events to keep in memory
            alert_callback: Function to call for alerts
        """
        self._events: deque = deque(maxlen=max_events)
        self._alert_callback = alert_callback
        self._stats = {
            "total_events": 0,
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "by_type": {},
            "alerts_sent": 0,
        }

    def record_event(
        self,
        event_type: str,
        severity: str,
        source: str,
        details: Optional[dict] = None
    ) -> SecurityEvent:
        """
        Record a security event.

        Args:
            event_type: Type of event
            severity: Severity level
            source: Event source
            details: Additional details

        Returns:
            Created SecurityEvent
        """
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            timestamp=time.time(),
            source=source,
            details=details or {}
        )

        self._events.append(event)
        self._stats["total_events"] += 1
        self._stats["by_severity"][severity] = self._stats["by_severity"].get(severity, 0) + 1
        self._stats["by_type"][event_type] = self._stats["by_type"].get(event_type, 0) + 1

        # Log the event
        log_msg = f"Security event: {event_type} ({severity}) from {source}"
        if severity == "critical":
            logger.critical(log_msg)
        elif severity == "high":
            logger.error(log_msg)
        elif severity == "medium":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        # Send alert for high-severity events
        if severity in ("critical", "high") and self._alert_callback:
            try:
                self._alert_callback(event)
                self._stats["alerts_sent"] += 1
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

        return event

    def get_recent_events(
        self,
        count: int = 100,
        severity_filter: Optional[str] = None,
        type_filter: Optional[str] = None
    ) -> list[SecurityEvent]:
        """
        Get recent security events.

        Args:
            count: Maximum events to return
            severity_filter: Filter by severity
            type_filter: Filter by event type

        Returns:
            List of events
        """
        events = list(self._events)

        if severity_filter:
            events = [e for e in events if e.severity == severity_filter]

        if type_filter:
            events = [e for e in events if e.event_type == type_filter]

        return list(reversed(events))[:count]

    def get_stats(self) -> dict:
        """Get security statistics."""
        return {
            **self._stats,
            "events_in_memory": len(self._events),
            "max_events": self._events.maxlen,
        }

    def get_threat_level(self) -> str:
        """
        Calculate current threat level based on recent events.

        Returns:
            Threat level (critical, high, elevated, normal)
        """
        # Look at last 100 events or last hour
        recent_events = self.get_recent_events(100)
        one_hour_ago = time.time() - 3600
        recent_events = [e for e in recent_events if e.timestamp > one_hour_ago]

        if not recent_events:
            return "normal"

        critical_count = sum(1 for e in recent_events if e.severity == "critical")
        high_count = sum(1 for e in recent_events if e.severity == "high")

        if critical_count > 0:
            return "critical"
        elif high_count >= 5:
            return "high"
        elif high_count > 0:
            return "elevated"

        return "normal"

    def clear_events(self):
        """Clear all recorded events."""
        self._events.clear()
        logger.info("Security events cleared")


# Global monitor instance
_monitor: Optional[SecurityMonitor] = None


def get_security_monitor() -> SecurityMonitor:
    """Get or create the security monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = SecurityMonitor()
    return _monitor


def record_security_event(
    event_type: str,
    severity: str,
    source: str,
    details: Optional[dict] = None
) -> SecurityEvent:
    """
    Convenience function to record a security event.

    Args:
        event_type: Type of event
        severity: Severity level
        source: Event source
        details: Additional details

    Returns:
        Created SecurityEvent
    """
    return get_security_monitor().record_event(event_type, severity, source, details)
