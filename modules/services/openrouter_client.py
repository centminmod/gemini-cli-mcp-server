"""
OpenRouter API client for 400+ AI models.

This module provides integration with OpenRouter for accessing models
from OpenAI, Anthropic, Meta, Google, and 20+ other providers.
"""
import json
import logging
import time
from typing import Optional
import httpx

from modules.config.gemini_config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_DEFAULT_MODEL,
    OPENROUTER_COST_LIMIT_PER_DAY,
    OPENROUTER_MAX_FILE_TOKENS,
    OPENROUTER_MAX_TOTAL_TOKENS,
)

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Client for OpenRouter API integration."""

    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.base_url = OPENROUTER_BASE_URL
        self.default_model = OPENROUTER_DEFAULT_MODEL
        self.max_file_tokens = OPENROUTER_MAX_FILE_TOKENS
        self.max_total_tokens = OPENROUTER_MAX_TOTAL_TOKENS
        self.daily_cost_limit = OPENROUTER_COST_LIMIT_PER_DAY

        # Usage tracking
        self._usage_stats = {
            "total_requests": 0,
            "total_tokens_in": 0,
            "total_tokens_out": 0,
            "total_cost": 0.0,
            "requests_by_model": {},
            "daily_cost": 0.0,
            "daily_reset_time": time.time(),
        }

        # Model cache
        self._models_cache = None
        self._models_cache_time = 0
        self._models_cache_ttl = 3600  # 1 hour

    def _check_configured(self) -> bool:
        """Check if OpenRouter is configured."""
        return bool(self.api_key)

    def _get_headers(self) -> dict:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/gemini-cli-mcp-server",
            "X-Title": "Gemini CLI MCP Server"
        }

    def _reset_daily_if_needed(self):
        """Reset daily stats if a day has passed."""
        if time.time() - self._usage_stats["daily_reset_time"] > 86400:
            self._usage_stats["daily_cost"] = 0.0
            self._usage_stats["daily_reset_time"] = time.time()

    def _check_budget(self) -> bool:
        """Check if within daily budget."""
        self._reset_daily_if_needed()
        return self._usage_stats["daily_cost"] < self.daily_cost_limit

    async def test_connection(self) -> dict:
        """Test OpenRouter connectivity."""
        if not self._check_configured():
            return {
                "status": "not_configured",
                "error": "OPENROUTER_API_KEY not set"
            }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self._get_headers(),
                    timeout=30.0
                )

            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "connected",
                    "models_available": len(data.get("data", [])),
                    "api_version": "v1"
                }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def get_opinion(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        file_handling_strategy: str = "auto"
    ) -> dict:
        """
        Get a response from an OpenRouter model.

        Args:
            prompt: The prompt (supports @filename syntax)
            model: Model ID
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            file_handling_strategy: Strategy for large files

        Returns:
            Response dictionary
        """
        if not self._check_configured():
            return {"error": "OpenRouter not configured"}

        if not self._check_budget():
            return {"error": f"Daily cost limit of ${self.daily_cost_limit} exceeded"}

        model = model or self.default_model

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                    timeout=300.0
                )

            if response.status_code == 200:
                data = response.json()

                # Track usage
                usage = data.get("usage", {})
                self._usage_stats["total_requests"] += 1
                self._usage_stats["total_tokens_in"] += usage.get("prompt_tokens", 0)
                self._usage_stats["total_tokens_out"] += usage.get("completion_tokens", 0)

                # Track per-model usage
                if model not in self._usage_stats["requests_by_model"]:
                    self._usage_stats["requests_by_model"][model] = 0
                self._usage_stats["requests_by_model"][model] += 1

                # Extract content
                content = ""
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")

                return {
                    "status": "success",
                    "model": model,
                    "content": content,
                    "usage": usage
                }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }

        except httpx.TimeoutException:
            return {"status": "error", "error": "Request timed out"}
        except Exception as e:
            logger.error(f"OpenRouter error: {e}")
            return {"status": "error", "error": str(e)}

    async def list_models(
        self,
        category: Optional[str] = None,
        provider_filter: Optional[str] = None,
        sort_by: str = "usage",
        include_pricing: bool = True
    ) -> dict:
        """
        List available OpenRouter models.

        Args:
            category: Filter by category
            provider_filter: Filter by provider
            sort_by: Sort order
            include_pricing: Include pricing info

        Returns:
            Model list dictionary
        """
        if not self._check_configured():
            return {"error": "OpenRouter not configured"}

        # Check cache
        if self._models_cache and time.time() - self._models_cache_time < self._models_cache_ttl:
            models = self._models_cache
        else:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/models",
                        headers=self._get_headers(),
                        timeout=30.0
                    )

                if response.status_code == 200:
                    data = response.json()
                    models = data.get("data", [])
                    self._models_cache = models
                    self._models_cache_time = time.time()
                else:
                    return {"error": f"HTTP {response.status_code}"}

            except Exception as e:
                return {"error": str(e)}

        # Filter models
        filtered_models = models

        if provider_filter:
            filtered_models = [
                m for m in filtered_models
                if m.get("id", "").startswith(f"{provider_filter}/")
            ]

        if category:
            # Simple category filtering based on model name/description
            category_lower = category.lower()
            filtered_models = [
                m for m in filtered_models
                if category_lower in m.get("id", "").lower()
                or category_lower in m.get("name", "").lower()
            ]

        # Sort models
        if sort_by == "price":
            filtered_models.sort(
                key=lambda m: m.get("pricing", {}).get("prompt", 0)
            )
        elif sort_by == "context_length":
            filtered_models.sort(
                key=lambda m: m.get("context_length", 0),
                reverse=True
            )
        elif sort_by == "name":
            filtered_models.sort(key=lambda m: m.get("id", ""))

        # Format response
        model_list = []
        for m in filtered_models[:100]:  # Limit to 100
            model_info = {
                "id": m.get("id"),
                "name": m.get("name"),
                "context_length": m.get("context_length"),
            }
            if include_pricing:
                model_info["pricing"] = m.get("pricing", {})
            model_list.append(model_info)

        return {
            "status": "success",
            "total_models": len(models),
            "filtered_count": len(filtered_models),
            "models": model_list
        }

    def get_usage_stats(self) -> dict:
        """Get usage statistics."""
        self._reset_daily_if_needed()
        return {
            **self._usage_stats,
            "daily_limit": self.daily_cost_limit,
            "daily_remaining": max(0, self.daily_cost_limit - self._usage_stats["daily_cost"])
        }


# Global client instance
_client: Optional[OpenRouterClient] = None


def get_openrouter_client() -> OpenRouterClient:
    """Get or create the OpenRouter client instance."""
    global _client
    if _client is None:
        _client = OpenRouterClient()
    return _client
