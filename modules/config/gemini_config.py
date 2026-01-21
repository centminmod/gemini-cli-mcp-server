"""
Main configuration interface for Gemini CLI MCP Server.

This module consolidates all configuration from environment variables
and provides a unified interface for the rest of the application.
"""
import os
from typing import Optional

# ============================================================================
# Core Configuration
# ============================================================================

GEMINI_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT", "300"))
GEMINI_COMMAND_PATH = os.getenv("GEMINI_COMMAND_PATH", "gemini")
GEMINI_LOG_LEVEL = os.getenv("GEMINI_LOG_LEVEL", "INFO").upper()
GEMINI_OUTPUT_FORMAT = os.getenv("GEMINI_OUTPUT_FORMAT", "json")

# ============================================================================
# Retry Configuration
# ============================================================================

RETRY_MAX_ATTEMPTS = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
RETRY_BASE_DELAY = float(os.getenv("RETRY_BASE_DELAY", "1.0"))
RETRY_MAX_DELAY = float(os.getenv("RETRY_MAX_DELAY", "30.0"))

# ============================================================================
# Tool-Specific Character Limits
# ============================================================================

GEMINI_PROMPT_LIMIT = int(os.getenv("GEMINI_PROMPT_LIMIT", "100000"))
GEMINI_SANDBOX_LIMIT = int(os.getenv("GEMINI_SANDBOX_LIMIT", "200000"))
GEMINI_SUMMARIZE_LIMIT = int(os.getenv("GEMINI_SUMMARIZE_LIMIT", "400000"))
GEMINI_SUMMARIZE_FILES_LIMIT = int(os.getenv("GEMINI_SUMMARIZE_FILES_LIMIT", "800000"))
GEMINI_EVAL_LIMIT = int(os.getenv("GEMINI_EVAL_LIMIT", "500000"))
GEMINI_REVIEW_LIMIT = int(os.getenv("GEMINI_REVIEW_LIMIT", "300000"))
GEMINI_VERIFY_LIMIT = int(os.getenv("GEMINI_VERIFY_LIMIT", "800000"))
GEMINI_COLLABORATION_LIMIT = int(os.getenv("GEMINI_COLLABORATION_LIMIT", "500000"))
GEMINI_CODE_REVIEW_LIMIT = int(os.getenv("GEMINI_CODE_REVIEW_LIMIT", "300000"))
GEMINI_EXTRACT_STRUCTURED_LIMIT = int(os.getenv("GEMINI_EXTRACT_STRUCTURED_LIMIT", "200000"))
GEMINI_GIT_DIFF_LIMIT = int(os.getenv("GEMINI_GIT_DIFF_LIMIT", "150000"))
GEMINI_CONTENT_COMPARISON_LIMIT = int(os.getenv("GEMINI_CONTENT_COMPARISON_LIMIT", "400000"))
GEMINI_OPENROUTER_OPINION_LIMIT = int(os.getenv("GEMINI_OPENROUTER_OPINION_LIMIT", "150000"))

# ============================================================================
# Model Configuration
# ============================================================================

DEFAULT_MODEL = os.getenv("GEMINI_DEFAULT_MODEL", "gemini-2.5-flash")
FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-2.5-flash")
ENABLE_FALLBACK = os.getenv("GEMINI_ENABLE_FALLBACK", "true").lower() == "true"

# Model scaling factors
MODEL_SCALING_FACTORS = {
    "gemini-2.5-pro": 1.0,
    "gemini-2.5-flash": 1.0,
    "gemini-1.5-pro": 0.8,
    "gemini-1.5-flash": 0.6,
    "gemini-1.0-pro": 0.4,
}


def get_model_scaling_factor(model: str) -> float:
    """Get the scaling factor for a model."""
    return MODEL_SCALING_FACTORS.get(model, 1.0)


# ============================================================================
# Rate Limiting Configuration
# ============================================================================

GEMINI_RATE_LIMIT_REQUESTS = int(os.getenv("GEMINI_RATE_LIMIT_REQUESTS", "100"))
GEMINI_RATE_LIMIT_WINDOW = int(os.getenv("GEMINI_RATE_LIMIT_WINDOW", "60"))

# ============================================================================
# OpenRouter Configuration
# ============================================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_DEFAULT_MODEL = os.getenv("OPENROUTER_DEFAULT_MODEL", "openai/gpt-4.1-nano")
OPENROUTER_COST_LIMIT_PER_DAY = float(os.getenv("OPENROUTER_COST_LIMIT_PER_DAY", "10.0"))
OPENROUTER_ENABLE_STREAMING = os.getenv("OPENROUTER_ENABLE_STREAMING", "true").lower() == "true"
OPENROUTER_MAX_FILE_TOKENS = int(os.getenv("OPENROUTER_MAX_FILE_TOKENS", "50000"))
OPENROUTER_MAX_TOTAL_TOKENS = int(os.getenv("OPENROUTER_MAX_TOTAL_TOKENS", "150000"))

# ============================================================================
# Conversation Management Configuration
# ============================================================================

GEMINI_CONVERSATION_ENABLED = os.getenv("GEMINI_CONVERSATION_ENABLED", "true").lower() == "true"
GEMINI_CONVERSATION_STORAGE = os.getenv("GEMINI_CONVERSATION_STORAGE", "memory")
GEMINI_CONVERSATION_EXPIRATION_HOURS = int(os.getenv("GEMINI_CONVERSATION_EXPIRATION_HOURS", "24"))
GEMINI_CONVERSATION_MAX_MESSAGES = int(os.getenv("GEMINI_CONVERSATION_MAX_MESSAGES", "10"))
GEMINI_CONVERSATION_MAX_TOKENS = int(os.getenv("GEMINI_CONVERSATION_MAX_TOKENS", "20000"))

# Redis Configuration
GEMINI_REDIS_HOST = os.getenv("GEMINI_REDIS_HOST", "localhost")
GEMINI_REDIS_PORT = int(os.getenv("GEMINI_REDIS_PORT", "6479"))
GEMINI_REDIS_DB = int(os.getenv("GEMINI_REDIS_DB", "0"))

# ============================================================================
# Cloudflare AI Gateway Configuration
# ============================================================================

CLOUDFLARE_AI_GATEWAY_ENABLED = os.getenv("CLOUDFLARE_AI_GATEWAY_ENABLED", "false").lower() == "true"
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
CLOUDFLARE_GATEWAY_ID = os.getenv("CLOUDFLARE_GATEWAY_ID", "")
CLOUDFLARE_AI_GATEWAY_TIMEOUT = int(os.getenv("CLOUDFLARE_AI_GATEWAY_TIMEOUT", "300"))
CLOUDFLARE_AI_GATEWAY_MAX_RETRIES = int(os.getenv("CLOUDFLARE_AI_GATEWAY_MAX_RETRIES", "3"))

# ============================================================================
# Monitoring Configuration
# ============================================================================

ENABLE_MONITORING = os.getenv("ENABLE_MONITORING", "false").lower() == "true"
ENABLE_OPENTELEMETRY = os.getenv("ENABLE_OPENTELEMETRY", "false").lower() == "true"
ENABLE_PROMETHEUS = os.getenv("ENABLE_PROMETHEUS", "false").lower() == "true"
ENABLE_HEALTH_CHECKS = os.getenv("ENABLE_HEALTH_CHECKS", "true").lower() == "true"
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "8000"))
OPENTELEMETRY_ENDPOINT = os.getenv("OPENTELEMETRY_ENDPOINT", "")
OPENTELEMETRY_SERVICE_NAME = os.getenv("OPENTELEMETRY_SERVICE_NAME", "gemini-cli-mcp-server")

# ============================================================================
# Security Configuration
# ============================================================================

JSONRPC_MAX_REQUEST_SIZE = int(os.getenv("JSONRPC_MAX_REQUEST_SIZE", "1048576"))
JSONRPC_MAX_NESTING_DEPTH = int(os.getenv("JSONRPC_MAX_NESTING_DEPTH", "10"))
JSONRPC_STRICT_MODE = os.getenv("JSONRPC_STRICT_MODE", "true").lower() == "true"
GEMINI_SUBPROCESS_MAX_CPU_TIME = int(os.getenv("GEMINI_SUBPROCESS_MAX_CPU_TIME", "300"))
GEMINI_SUBPROCESS_MAX_MEMORY_MB = int(os.getenv("GEMINI_SUBPROCESS_MAX_MEMORY_MB", "512"))


def get_config_summary() -> dict:
    """Get a summary of current configuration."""
    return {
        "core": {
            "timeout": GEMINI_TIMEOUT,
            "command_path": GEMINI_COMMAND_PATH,
            "log_level": GEMINI_LOG_LEVEL,
            "output_format": GEMINI_OUTPUT_FORMAT,
        },
        "limits": {
            "prompt": GEMINI_PROMPT_LIMIT,
            "sandbox": GEMINI_SANDBOX_LIMIT,
            "summarize": GEMINI_SUMMARIZE_LIMIT,
            "summarize_files": GEMINI_SUMMARIZE_FILES_LIMIT,
            "eval": GEMINI_EVAL_LIMIT,
            "review": GEMINI_REVIEW_LIMIT,
            "verify": GEMINI_VERIFY_LIMIT,
            "collaboration": GEMINI_COLLABORATION_LIMIT,
        },
        "models": {
            "default": DEFAULT_MODEL,
            "fallback": FALLBACK_MODEL,
            "fallback_enabled": ENABLE_FALLBACK,
        },
        "rate_limiting": {
            "requests": GEMINI_RATE_LIMIT_REQUESTS,
            "window_seconds": GEMINI_RATE_LIMIT_WINDOW,
        },
        "openrouter": {
            "configured": bool(OPENROUTER_API_KEY),
            "default_model": OPENROUTER_DEFAULT_MODEL,
            "daily_limit": OPENROUTER_COST_LIMIT_PER_DAY,
        },
        "conversations": {
            "enabled": GEMINI_CONVERSATION_ENABLED,
            "storage": GEMINI_CONVERSATION_STORAGE,
            "expiration_hours": GEMINI_CONVERSATION_EXPIRATION_HOURS,
        },
        "monitoring": {
            "enabled": ENABLE_MONITORING,
            "opentelemetry": ENABLE_OPENTELEMETRY,
            "prometheus": ENABLE_PROMETHEUS,
        },
    }
