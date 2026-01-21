"""
OpenTelemetry, Prometheus, and health check integration.

This module provides enterprise monitoring capabilities.
"""
import logging
import time
from typing import Optional, Callable
from dataclasses import dataclass, field

from modules.config.feature_config import (
    FEATURE_MONITORING_ENABLED,
    FEATURE_OPENTELEMETRY_ENABLED,
    FEATURE_PROMETHEUS_ENABLED,
    FEATURE_HEALTH_CHECKS_ENABLED,
    MONITORING_CONFIG,
)

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    healthy: bool
    message: str
    duration_ms: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class MetricPoint:
    """A single metric data point."""
    name: str
    value: float
    labels: dict
    timestamp: float = field(default_factory=time.time)


class MonitoringService:
    """Central monitoring service for the MCP server."""

    def __init__(self):
        self.enabled = FEATURE_MONITORING_ENABLED
        self._metrics: dict[str, list[MetricPoint]] = {}
        self._health_checks: dict[str, Callable] = {}
        self._last_health_results: dict[str, HealthCheckResult] = {}

        # Counters
        self._counters = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_error": 0,
            "tools_invoked": {},
        }

        # Histograms (simplified)
        self._histograms = {
            "request_duration_ms": [],
            "tool_duration_ms": {},
        }

        # Initialize subsystems
        self._init_opentelemetry()
        self._init_prometheus()
        self._register_default_health_checks()

    def _init_opentelemetry(self):
        """Initialize OpenTelemetry if enabled."""
        if not FEATURE_OPENTELEMETRY_ENABLED:
            self._tracer = None
            return

        try:
            # OpenTelemetry initialization would go here
            # This is a placeholder for actual OTel setup
            logger.info("OpenTelemetry monitoring initialized (placeholder)")
            self._tracer = None  # Would be actual tracer
        except ImportError:
            logger.warning("OpenTelemetry packages not installed")
            self._tracer = None

    def _init_prometheus(self):
        """Initialize Prometheus metrics if enabled."""
        if not FEATURE_PROMETHEUS_ENABLED:
            self._prometheus_registry = None
            return

        try:
            # Prometheus initialization would go here
            logger.info("Prometheus monitoring initialized (placeholder)")
            self._prometheus_registry = None  # Would be actual registry
        except ImportError:
            logger.warning("Prometheus client not installed")
            self._prometheus_registry = None

    def _register_default_health_checks(self):
        """Register default health checks."""
        if not FEATURE_HEALTH_CHECKS_ENABLED:
            return

        self.register_health_check("server", self._check_server_health)
        self.register_health_check("gemini_cli", self._check_gemini_cli)

    def _check_server_health(self) -> HealthCheckResult:
        """Check server health."""
        start = time.time()
        try:
            # Basic server health check
            return HealthCheckResult(
                name="server",
                healthy=True,
                message="Server is running",
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return HealthCheckResult(
                name="server",
                healthy=False,
                message=str(e),
                duration_ms=(time.time() - start) * 1000
            )

    def _check_gemini_cli(self) -> HealthCheckResult:
        """Check Gemini CLI availability."""
        start = time.time()
        try:
            from modules.utils.gemini_utils import validate_gemini_setup
            is_healthy = validate_gemini_setup()
            return HealthCheckResult(
                name="gemini_cli",
                healthy=is_healthy,
                message="Gemini CLI available" if is_healthy else "Gemini CLI not found",
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return HealthCheckResult(
                name="gemini_cli",
                healthy=False,
                message=str(e),
                duration_ms=(time.time() - start) * 1000
            )

    def register_health_check(self, name: str, check_func: Callable):
        """Register a health check function."""
        self._health_checks[name] = check_func
        logger.debug(f"Registered health check: {name}")

    def run_health_checks(self) -> dict:
        """Run all health checks."""
        results = {}
        overall_healthy = True

        for name, check_func in self._health_checks.items():
            try:
                result = check_func()
                results[name] = {
                    "healthy": result.healthy,
                    "message": result.message,
                    "duration_ms": result.duration_ms
                }
                self._last_health_results[name] = result
                if not result.healthy:
                    overall_healthy = False
            except Exception as e:
                results[name] = {
                    "healthy": False,
                    "message": f"Check failed: {str(e)}",
                    "duration_ms": 0
                }
                overall_healthy = False

        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": time.time(),
            "checks": results
        }

    def record_request(self, tool_name: str, duration_ms: float, success: bool):
        """Record a request metric."""
        self._counters["requests_total"] += 1
        if success:
            self._counters["requests_success"] += 1
        else:
            self._counters["requests_error"] += 1

        # Track per-tool metrics
        if tool_name not in self._counters["tools_invoked"]:
            self._counters["tools_invoked"][tool_name] = 0
        self._counters["tools_invoked"][tool_name] += 1

        # Record duration
        self._histograms["request_duration_ms"].append(duration_ms)
        if len(self._histograms["request_duration_ms"]) > 10000:
            self._histograms["request_duration_ms"] = self._histograms["request_duration_ms"][-5000:]

        if tool_name not in self._histograms["tool_duration_ms"]:
            self._histograms["tool_duration_ms"][tool_name] = []
        self._histograms["tool_duration_ms"][tool_name].append(duration_ms)
        if len(self._histograms["tool_duration_ms"][tool_name]) > 1000:
            self._histograms["tool_duration_ms"][tool_name] = \
                self._histograms["tool_duration_ms"][tool_name][-500:]

    def record_metric(self, name: str, value: float, labels: Optional[dict] = None):
        """Record a custom metric."""
        point = MetricPoint(
            name=name,
            value=value,
            labels=labels or {}
        )

        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(point)

        # Limit stored points
        if len(self._metrics[name]) > 1000:
            self._metrics[name] = self._metrics[name][-500:]

    def get_metrics(self) -> dict:
        """Get all metrics."""
        # Calculate averages for histograms
        request_durations = self._histograms["request_duration_ms"]
        avg_duration = sum(request_durations) / len(request_durations) if request_durations else 0

        tool_avg_durations = {}
        for tool, durations in self._histograms["tool_duration_ms"].items():
            tool_avg_durations[tool] = sum(durations) / len(durations) if durations else 0

        return {
            "counters": self._counters,
            "histograms": {
                "request_duration_avg_ms": avg_duration,
                "tool_duration_avg_ms": tool_avg_durations,
            },
            "custom_metrics": {
                name: [{"value": p.value, "labels": p.labels} for p in points[-10:]]
                for name, points in self._metrics.items()
            }
        }

    def get_status(self) -> dict:
        """Get monitoring status."""
        return {
            "enabled": self.enabled,
            "opentelemetry": {
                "enabled": FEATURE_OPENTELEMETRY_ENABLED,
                "active": self._tracer is not None
            },
            "prometheus": {
                "enabled": FEATURE_PROMETHEUS_ENABLED,
                "active": self._prometheus_registry is not None
            },
            "health_checks": {
                "enabled": FEATURE_HEALTH_CHECKS_ENABLED,
                "registered": list(self._health_checks.keys())
            }
        }


# Global monitoring service
_service: Optional[MonitoringService] = None


def get_monitoring_service() -> MonitoringService:
    """Get or create the monitoring service."""
    global _service
    if _service is None:
        _service = MonitoringService()
    return _service


def record_request_metric(tool_name: str, duration_ms: float, success: bool):
    """Convenience function to record a request metric."""
    get_monitoring_service().record_request(tool_name, duration_ms, success)


def get_health_status() -> dict:
    """Convenience function to get health status."""
    return get_monitoring_service().run_health_checks()
