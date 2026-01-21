"""
JSON-RPC security validation.

This module provides security validation for JSON-RPC requests.
"""
import json
import logging
from typing import Optional, Tuple, Any

from modules.config.gemini_config import (
    JSONRPC_MAX_REQUEST_SIZE,
    JSONRPC_MAX_NESTING_DEPTH,
    JSONRPC_STRICT_MODE,
)

logger = logging.getLogger(__name__)


class JSONRPCValidator:
    """Validates JSON-RPC requests for security issues."""

    def __init__(
        self,
        max_request_size: int = JSONRPC_MAX_REQUEST_SIZE,
        max_nesting_depth: int = JSONRPC_MAX_NESTING_DEPTH,
        strict_mode: bool = JSONRPC_STRICT_MODE
    ):
        """
        Initialize validator.

        Args:
            max_request_size: Maximum request size in bytes
            max_nesting_depth: Maximum object nesting depth
            strict_mode: Enable strict JSON-RPC validation
        """
        self.max_request_size = max_request_size
        self.max_nesting_depth = max_nesting_depth
        self.strict_mode = strict_mode

    def validate_request(self, request: str | dict) -> Tuple[bool, list[str]]:
        """
        Validate a JSON-RPC request.

        Args:
            request: JSON-RPC request (string or dict)

        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []

        # Convert string to dict if needed
        if isinstance(request, str):
            # Check size
            if len(request) > self.max_request_size:
                issues.append(f"Request exceeds maximum size of {self.max_request_size} bytes")
                return False, issues

            try:
                request = json.loads(request)
            except json.JSONDecodeError as e:
                issues.append(f"Invalid JSON: {str(e)}")
                return False, issues

        # Validate JSON-RPC structure
        if not isinstance(request, dict):
            issues.append("Request must be a JSON object")
            return False, issues

        # Check required fields
        if "jsonrpc" not in request:
            issues.append("Missing 'jsonrpc' field")
        elif request.get("jsonrpc") != "2.0":
            issues.append("Invalid JSON-RPC version (must be '2.0')")

        if "method" not in request:
            issues.append("Missing 'method' field")
        elif not isinstance(request.get("method"), str):
            issues.append("'method' must be a string")
        elif request.get("method", "").startswith("rpc."):
            issues.append("Methods starting with 'rpc.' are reserved")

        # Check nesting depth
        depth = self._get_nesting_depth(request)
        if depth > self.max_nesting_depth:
            issues.append(f"Nesting depth {depth} exceeds maximum of {self.max_nesting_depth}")

        # Strict mode checks
        if self.strict_mode:
            if "id" not in request:
                issues.append("Missing 'id' field (required in strict mode)")

            # Check for unexpected fields
            allowed_fields = {"jsonrpc", "method", "params", "id"}
            extra_fields = set(request.keys()) - allowed_fields
            if extra_fields:
                issues.append(f"Unexpected fields: {extra_fields}")

        is_valid = len(issues) == 0
        return is_valid, issues

    def _get_nesting_depth(self, obj: Any, current_depth: int = 0) -> int:
        """
        Calculate nesting depth of an object.

        Args:
            obj: Object to analyze
            current_depth: Current depth

        Returns:
            Maximum nesting depth
        """
        if current_depth > self.max_nesting_depth + 1:
            # Short-circuit to avoid DoS
            return current_depth

        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(
                self._get_nesting_depth(v, current_depth + 1)
                for v in obj.values()
            )
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(
                self._get_nesting_depth(item, current_depth + 1)
                for item in obj
            )
        else:
            return current_depth

    def validate_response(self, response: dict) -> Tuple[bool, list[str]]:
        """
        Validate a JSON-RPC response.

        Args:
            response: JSON-RPC response dict

        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []

        if not isinstance(response, dict):
            issues.append("Response must be a JSON object")
            return False, issues

        # Check required fields
        if "jsonrpc" not in response:
            issues.append("Missing 'jsonrpc' field")
        elif response.get("jsonrpc") != "2.0":
            issues.append("Invalid JSON-RPC version")

        if "id" not in response:
            issues.append("Missing 'id' field")

        # Must have either result or error
        has_result = "result" in response
        has_error = "error" in response

        if has_result and has_error:
            issues.append("Response cannot have both 'result' and 'error'")
        elif not has_result and not has_error:
            issues.append("Response must have either 'result' or 'error'")

        # Validate error structure
        if has_error:
            error = response.get("error", {})
            if not isinstance(error, dict):
                issues.append("'error' must be an object")
            else:
                if "code" not in error:
                    issues.append("Error missing 'code' field")
                elif not isinstance(error.get("code"), int):
                    issues.append("Error 'code' must be an integer")

                if "message" not in error:
                    issues.append("Error missing 'message' field")
                elif not isinstance(error.get("message"), str):
                    issues.append("Error 'message' must be a string")

        is_valid = len(issues) == 0
        return is_valid, issues


# Global validator instance
_validator = JSONRPCValidator()


def validate_jsonrpc_request(request: str | dict) -> Tuple[bool, list[str]]:
    """
    Convenience function to validate a JSON-RPC request.

    Args:
        request: JSON-RPC request

    Returns:
        Tuple of (is_valid, list of issues)
    """
    return _validator.validate_request(request)


def validate_jsonrpc_response(response: dict) -> Tuple[bool, list[str]]:
    """
    Convenience function to validate a JSON-RPC response.

    Args:
        response: JSON-RPC response

    Returns:
        Tuple of (is_valid, list of issues)
    """
    return _validator.validate_response(response)
