"""
Feature flags and feature-specific configuration.

This module manages feature toggles and feature-specific settings.
"""
import os

# ============================================================================
# Feature Flags
# ============================================================================

# OpenRouter Integration
FEATURE_OPENROUTER_ENABLED = bool(os.getenv("OPENROUTER_API_KEY", ""))
FEATURE_OPENROUTER_STREAMING = os.getenv("OPENROUTER_ENABLE_STREAMING", "true").lower() == "true"

# Conversation Management
FEATURE_CONVERSATIONS_ENABLED = os.getenv("GEMINI_CONVERSATION_ENABLED", "true").lower() == "true"

# Monitoring Features
FEATURE_MONITORING_ENABLED = os.getenv("ENABLE_MONITORING", "false").lower() == "true"
FEATURE_OPENTELEMETRY_ENABLED = os.getenv("ENABLE_OPENTELEMETRY", "false").lower() == "true"
FEATURE_PROMETHEUS_ENABLED = os.getenv("ENABLE_PROMETHEUS", "false").lower() == "true"
FEATURE_HEALTH_CHECKS_ENABLED = os.getenv("ENABLE_HEALTH_CHECKS", "true").lower() == "true"

# Security Features
FEATURE_JSONRPC_VALIDATION = os.getenv("JSONRPC_STRICT_MODE", "true").lower() == "true"
FEATURE_CREDENTIAL_SANITIZATION = True  # Always enabled
FEATURE_RATE_LIMITING = os.getenv("GEMINI_RATE_LIMIT_REQUESTS", "100") != "0"

# Cloudflare AI Gateway
FEATURE_CLOUDFLARE_GATEWAY = os.getenv("CLOUDFLARE_AI_GATEWAY_ENABLED", "false").lower() == "true"

# Redis Support
FEATURE_REDIS_ENABLED = os.getenv("GEMINI_CONVERSATION_STORAGE", "memory").lower() == "redis"

# Model Fallback
FEATURE_MODEL_FALLBACK = os.getenv("GEMINI_ENABLE_FALLBACK", "true").lower() == "true"

# ============================================================================
# OpenRouter Feature Configuration
# ============================================================================

OPENROUTER_CONFIG = {
    "api_key": os.getenv("OPENROUTER_API_KEY", ""),
    "base_url": os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    "default_model": os.getenv("OPENROUTER_DEFAULT_MODEL", "openai/gpt-4.1-nano"),
    "daily_cost_limit": float(os.getenv("OPENROUTER_COST_LIMIT_PER_DAY", "10.0")),
    "max_file_tokens": int(os.getenv("OPENROUTER_MAX_FILE_TOKENS", "50000")),
    "max_total_tokens": int(os.getenv("OPENROUTER_MAX_TOTAL_TOKENS", "150000")),
    "streaming_enabled": os.getenv("OPENROUTER_ENABLE_STREAMING", "true").lower() == "true",
    "timeout": int(os.getenv("OPENROUTER_TIMEOUT", "300")),
}

# ============================================================================
# Monitoring Feature Configuration
# ============================================================================

MONITORING_CONFIG = {
    "enabled": FEATURE_MONITORING_ENABLED,
    "opentelemetry": {
        "enabled": FEATURE_OPENTELEMETRY_ENABLED,
        "endpoint": os.getenv("OPENTELEMETRY_ENDPOINT", ""),
        "service_name": os.getenv("OPENTELEMETRY_SERVICE_NAME", "gemini-cli-mcp-server"),
    },
    "prometheus": {
        "enabled": FEATURE_PROMETHEUS_ENABLED,
        "port": int(os.getenv("PROMETHEUS_PORT", "8000")),
    },
    "health_checks": {
        "enabled": FEATURE_HEALTH_CHECKS_ENABLED,
        "interval_seconds": int(os.getenv("HEALTH_CHECK_INTERVAL", "30")),
    },
}

# ============================================================================
# Conversation Feature Configuration
# ============================================================================

CONVERSATION_CONFIG = {
    "enabled": FEATURE_CONVERSATIONS_ENABLED,
    "storage_backend": os.getenv("GEMINI_CONVERSATION_STORAGE", "memory"),
    "expiration_hours": int(os.getenv("GEMINI_CONVERSATION_EXPIRATION_HOURS", "24")),
    "max_messages": int(os.getenv("GEMINI_CONVERSATION_MAX_MESSAGES", "10")),
    "max_tokens": int(os.getenv("GEMINI_CONVERSATION_MAX_TOKENS", "20000")),
    "redis": {
        "host": os.getenv("GEMINI_REDIS_HOST", "localhost"),
        "port": int(os.getenv("GEMINI_REDIS_PORT", "6479")),
        "db": int(os.getenv("GEMINI_REDIS_DB", "0")),
    },
}

# ============================================================================
# Cloudflare Gateway Configuration
# ============================================================================

CLOUDFLARE_CONFIG = {
    "enabled": FEATURE_CLOUDFLARE_GATEWAY,
    "account_id": os.getenv("CLOUDFLARE_ACCOUNT_ID", ""),
    "gateway_id": os.getenv("CLOUDFLARE_GATEWAY_ID", ""),
    "timeout": int(os.getenv("CLOUDFLARE_AI_GATEWAY_TIMEOUT", "300")),
    "max_retries": int(os.getenv("CLOUDFLARE_AI_GATEWAY_MAX_RETRIES", "3")),
}


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled."""
    feature_map = {
        "openrouter": FEATURE_OPENROUTER_ENABLED,
        "conversations": FEATURE_CONVERSATIONS_ENABLED,
        "monitoring": FEATURE_MONITORING_ENABLED,
        "opentelemetry": FEATURE_OPENTELEMETRY_ENABLED,
        "prometheus": FEATURE_PROMETHEUS_ENABLED,
        "health_checks": FEATURE_HEALTH_CHECKS_ENABLED,
        "jsonrpc_validation": FEATURE_JSONRPC_VALIDATION,
        "rate_limiting": FEATURE_RATE_LIMITING,
        "cloudflare_gateway": FEATURE_CLOUDFLARE_GATEWAY,
        "redis": FEATURE_REDIS_ENABLED,
        "model_fallback": FEATURE_MODEL_FALLBACK,
    }
    return feature_map.get(feature_name, False)


def get_feature_status() -> dict:
    """Get status of all features."""
    return {
        "openrouter": {
            "enabled": FEATURE_OPENROUTER_ENABLED,
            "streaming": FEATURE_OPENROUTER_STREAMING,
        },
        "conversations": {
            "enabled": FEATURE_CONVERSATIONS_ENABLED,
            "redis": FEATURE_REDIS_ENABLED,
        },
        "monitoring": {
            "enabled": FEATURE_MONITORING_ENABLED,
            "opentelemetry": FEATURE_OPENTELEMETRY_ENABLED,
            "prometheus": FEATURE_PROMETHEUS_ENABLED,
            "health_checks": FEATURE_HEALTH_CHECKS_ENABLED,
        },
        "security": {
            "jsonrpc_validation": FEATURE_JSONRPC_VALIDATION,
            "credential_sanitization": FEATURE_CREDENTIAL_SANITIZATION,
            "rate_limiting": FEATURE_RATE_LIMITING,
        },
        "integrations": {
            "cloudflare_gateway": FEATURE_CLOUDFLARE_GATEWAY,
            "model_fallback": FEATURE_MODEL_FALLBACK,
        },
    }
