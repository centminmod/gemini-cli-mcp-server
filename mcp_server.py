"""
Gemini CLI MCP Server

A production-ready Model Context Protocol (MCP) server that bridges Google's
Gemini CLI with MCP-compatible clients like Claude Code and Claude Desktop.

This server provides 33 specialized tools for seamless multi-AI workflows.
"""
import sys
from pathlib import Path

# Ensure imports work regardless of working directory
script_dir = Path(__file__).parent.resolve()
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

import os
import json
import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP

# Configure logging
log_level = os.getenv("GEMINI_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("gemini-cli-mcp-server")

# Import utilities
from modules.utils.gemini_utils import (
    execute_gemini,
    execute_gemini_with_retry,
    get_gemini_help,
    get_gemini_version,
    get_metrics,
    validate_gemini_setup,
    GeminiExecutionError,
    GeminiTimeoutError,
    GeminiRateLimitError,
)

# ============================================================================
# PHASE 1: Core CLI Tools (gemini_cli, gemini_help, gemini_version)
# ============================================================================

@mcp.tool()
async def gemini_cli(command: str) -> str:
    """
    Execute any Gemini CLI command directly with comprehensive error handling.

    Args:
        command: The Gemini CLI command to execute (without the 'gemini' prefix)

    Returns:
        JSON string with status, stdout, stderr, and return_code

    Examples:
        gemini_cli(command="--prompt 'Hello world'")
        gemini_cli(command="--model gemini-2.5-pro --prompt 'Explain AI'")
    """
    if not command or not command.strip():
        return json.dumps({
            "status": "error",
            "error": "Command cannot be empty",
            "error_code": "INVALID_INPUT"
        })

    try:
        import shlex
        args = shlex.split(command)
    except ValueError as e:
        return json.dumps({
            "status": "error",
            "error": f"Invalid command format: {str(e)}",
            "error_code": "INVALID_COMMAND"
        })

    try:
        result = await execute_gemini_with_retry(args)
        return json.dumps(result, indent=2)
    except GeminiTimeoutError as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "error_code": "TIMEOUT"
        })
    except GeminiRateLimitError as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "error_code": "RATE_LIMIT"
        })
    except GeminiExecutionError as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "error_code": "EXECUTION_ERROR"
        })
    except Exception as e:
        logger.error(f"Unexpected error in gemini_cli: {e}")
        return json.dumps({
            "status": "error",
            "error": "An unexpected error occurred",
            "error_code": "INTERNAL_ERROR"
        })


@mcp.tool()
async def gemini_help() -> str:
    """
    Get cached Gemini CLI help information (30-minute TTL).

    Returns:
        Gemini CLI help text

    Examples:
        gemini_help()
    """
    try:
        help_text = await get_gemini_help()
        return help_text
    except GeminiExecutionError as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "error_code": "EXECUTION_ERROR"
        })
    except Exception as e:
        logger.error(f"Unexpected error in gemini_help: {e}")
        return json.dumps({
            "status": "error",
            "error": "Failed to get help",
            "error_code": "INTERNAL_ERROR"
        })


@mcp.tool()
async def gemini_version() -> str:
    """
    Get cached Gemini CLI version information (30-minute TTL).

    Returns:
        Gemini CLI version information

    Examples:
        gemini_version()
    """
    try:
        version_text = await get_gemini_version()
        return version_text
    except GeminiExecutionError as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "error_code": "EXECUTION_ERROR"
        })
    except Exception as e:
        logger.error(f"Unexpected error in gemini_version: {e}")
        return json.dumps({
            "status": "error",
            "error": "Failed to get version",
            "error_code": "INTERNAL_ERROR"
        })


# ============================================================================
# PHASE 2: Core Tools (gemini_prompt, gemini_models, gemini_metrics)
# ============================================================================

# Import configuration when available
try:
    from modules.config.gemini_config import (
        GEMINI_PROMPT_LIMIT,
        GEMINI_SANDBOX_LIMIT,
        GEMINI_SUMMARIZE_LIMIT,
        GEMINI_SUMMARIZE_FILES_LIMIT,
        GEMINI_EVAL_LIMIT,
        GEMINI_REVIEW_LIMIT,
        GEMINI_VERIFY_LIMIT,
        GEMINI_COLLABORATION_LIMIT,
        DEFAULT_MODEL,
        FALLBACK_MODEL,
        get_model_scaling_factor,
    )
except ImportError:
    # Default limits if config not yet available
    GEMINI_PROMPT_LIMIT = 100000
    GEMINI_SANDBOX_LIMIT = 200000
    GEMINI_SUMMARIZE_LIMIT = 400000
    GEMINI_SUMMARIZE_FILES_LIMIT = 800000
    GEMINI_EVAL_LIMIT = 500000
    GEMINI_REVIEW_LIMIT = 300000
    GEMINI_VERIFY_LIMIT = 800000
    GEMINI_COLLABORATION_LIMIT = 500000
    DEFAULT_MODEL = "gemini-2.5-flash"
    FALLBACK_MODEL = "gemini-2.5-flash"

    def get_model_scaling_factor(model: str) -> float:
        return 1.0


@mcp.tool()
async def gemini_prompt(
    prompt: str,
    model: Optional[str] = None,
    sandbox: bool = False,
    debug: bool = False
) -> str:
    """
    Send prompts with structured parameters and validation (100,000 char limit).

    Args:
        prompt: The prompt to send to Gemini
        model: Optional model to use (default: gemini-2.5-flash)
        sandbox: Whether to run in sandbox mode
        debug: Whether to enable debug output

    Returns:
        JSON string with the response

    Examples:
        gemini_prompt(prompt="Explain quantum computing")
        gemini_prompt(prompt="Analyze this code", model="gemini-2.5-pro")
    """
    model = model or DEFAULT_MODEL
    scaling_factor = get_model_scaling_factor(model)
    effective_limit = int(GEMINI_PROMPT_LIMIT * scaling_factor)

    if len(prompt) > effective_limit:
        return json.dumps({
            "status": "error",
            "error": f"Prompt exceeds limit of {effective_limit:,} characters "
                     f"(got {len(prompt):,})",
            "error_code": "INPUT_TOO_LARGE"
        })

    args = []
    if model:
        args.extend(["--model", model])
    if sandbox:
        args.append("--sandbox")
    if debug:
        args.append("--debug")
    args.extend(["--prompt", prompt])

    try:
        result = await execute_gemini_with_retry(
            args,
            fallback_model=FALLBACK_MODEL if model != FALLBACK_MODEL else None
        )
        return json.dumps(result, indent=2)
    except GeminiTimeoutError as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "error_code": "TIMEOUT"
        })
    except GeminiRateLimitError as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "error_code": "RATE_LIMIT"
        })
    except GeminiExecutionError as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "error_code": "EXECUTION_ERROR"
        })


@mcp.tool()
async def gemini_models() -> str:
    """
    List all available Gemini AI models.

    Returns:
        List of available models with their capabilities

    Examples:
        gemini_models()
    """
    # Import model config when available
    try:
        from modules.config.model_config import GEMINI_MODELS
        return json.dumps({
            "status": "success",
            "models": GEMINI_MODELS
        }, indent=2)
    except ImportError:
        # Default model list
        models = {
            "gemini-2.5-pro": {
                "description": "Most capable model for complex tasks",
                "context_window": "1M tokens",
                "scaling_factor": 1.0,
                "best_for": ["complex analysis", "code review", "creative tasks"]
            },
            "gemini-2.5-flash": {
                "description": "Fast, efficient model for most tasks",
                "context_window": "1M tokens",
                "scaling_factor": 1.0,
                "best_for": ["quick responses", "simple tasks", "high throughput"]
            },
            "gemini-1.5-pro": {
                "description": "Stable production model",
                "context_window": "128K tokens",
                "scaling_factor": 0.8,
                "best_for": ["production workloads", "reliability"]
            },
            "gemini-1.5-flash": {
                "description": "Fast model for simpler tasks",
                "context_window": "128K tokens",
                "scaling_factor": 0.6,
                "best_for": ["speed-critical tasks", "simple queries"]
            }
        }
        return json.dumps({
            "status": "success",
            "models": models
        }, indent=2)


@mcp.tool()
async def gemini_metrics() -> str:
    """
    Get comprehensive server performance metrics and statistics.

    Returns:
        JSON with server metrics including execution stats, cache stats, etc.

    Examples:
        gemini_metrics()
    """
    try:
        metrics = get_metrics()

        # Add cache-specific stats
        from modules.utils.gemini_utils import HELP_CACHE, VERSION_CACHE, PROMPT_CACHE

        cache_stats = {
            "help_cache": {
                "size": len(HELP_CACHE),
                "maxsize": HELP_CACHE.maxsize,
                "ttl": HELP_CACHE.ttl
            },
            "version_cache": {
                "size": len(VERSION_CACHE),
                "maxsize": VERSION_CACHE.maxsize,
                "ttl": VERSION_CACHE.ttl
            },
            "prompt_cache": {
                "size": len(PROMPT_CACHE),
                "maxsize": PROMPT_CACHE.maxsize,
                "ttl": PROMPT_CACHE.ttl
            }
        }

        return json.dumps({
            "status": "success",
            "metrics": metrics,
            "cache_stats": cache_stats,
            "server_info": {
                "name": "gemini-cli-mcp-server",
                "tools_available": 33,
                "python_version": os.sys.version
            }
        }, indent=2)
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return json.dumps({
            "status": "error",
            "error": str(e),
            "error_code": "METRICS_ERROR"
        })


# ============================================================================
# PHASE 3: System Tools
# ============================================================================

@mcp.tool()
async def gemini_sandbox(
    prompt: str,
    model: Optional[str] = None,
    sandbox_image: Optional[str] = None
) -> str:
    """
    Execute prompts in sandbox mode for code execution (200,000 char limit).

    Args:
        prompt: The prompt to execute in sandbox mode
        model: Optional model to use (default: gemini-2.5-pro)
        sandbox_image: Optional Docker image for sandbox (e.g., python:3.11-slim)

    Returns:
        JSON string with execution results

    Examples:
        gemini_sandbox(prompt="Write and run a Python script to analyze data")
        gemini_sandbox(prompt="Test this code", sandbox_image="node:18-alpine")
    """
    model = model or "gemini-2.5-pro"
    scaling_factor = get_model_scaling_factor(model)
    effective_limit = int(GEMINI_SANDBOX_LIMIT * scaling_factor)

    if len(prompt) > effective_limit:
        return json.dumps({
            "status": "error",
            "error": f"Prompt exceeds limit of {effective_limit:,} characters",
            "error_code": "INPUT_TOO_LARGE"
        })

    args = ["--model", model, "--sandbox"]
    if sandbox_image:
        args.extend(["--sandbox-image", sandbox_image])
    args.extend(["--prompt", prompt])

    try:
        result = await execute_gemini_with_retry(args, fallback_model=FALLBACK_MODEL)
        return json.dumps(result, indent=2)
    except (GeminiTimeoutError, GeminiRateLimitError, GeminiExecutionError) as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "error_code": type(e).__name__.replace("Gemini", "").replace("Error", "").upper()
        })


@mcp.tool()
async def gemini_cache_stats() -> str:
    """
    Get cache statistics for all cache backends.

    Returns:
        JSON with cache statistics for all caches

    Examples:
        gemini_cache_stats()
    """
    from modules.utils.gemini_utils import HELP_CACHE, VERSION_CACHE, PROMPT_CACHE

    stats = {
        "help_cache": {
            "size": len(HELP_CACHE),
            "maxsize": HELP_CACHE.maxsize,
            "ttl_seconds": HELP_CACHE.ttl,
            "items": list(HELP_CACHE.keys())
        },
        "version_cache": {
            "size": len(VERSION_CACHE),
            "maxsize": VERSION_CACHE.maxsize,
            "ttl_seconds": VERSION_CACHE.ttl,
            "items": list(VERSION_CACHE.keys())
        },
        "prompt_cache": {
            "size": len(PROMPT_CACHE),
            "maxsize": PROMPT_CACHE.maxsize,
            "ttl_seconds": PROMPT_CACHE.ttl,
            "item_count": len(PROMPT_CACHE)
        }
    }

    # Try to get Redis cache stats if available
    try:
        from modules.services.redis_cache import get_redis_stats
        stats["redis_cache"] = get_redis_stats()
    except ImportError:
        stats["redis_cache"] = {"status": "not_configured"}

    return json.dumps({
        "status": "success",
        "cache_statistics": stats
    }, indent=2)


@mcp.tool()
async def gemini_rate_limiting_stats() -> str:
    """
    Get comprehensive rate limiting and quota statistics.

    Returns:
        JSON with rate limiting statistics

    Examples:
        gemini_rate_limiting_stats()
    """
    metrics = get_metrics()

    rate_stats = {
        "rate_limit_hits": metrics.get("rate_limit_hits", 0),
        "fallback_count": metrics.get("fallback_count", 0),
        "commands_executed": metrics.get("commands_executed", 0),
        "success_rate": metrics.get("success_rate", 0),
    }

    # Try to get per-model rate limiting stats
    try:
        from modules.services.per_model_rate_limiter import get_rate_limit_stats
        rate_stats["per_model_stats"] = get_rate_limit_stats()
    except ImportError:
        rate_stats["per_model_stats"] = {"status": "not_configured"}

    return json.dumps({
        "status": "success",
        "rate_limiting_statistics": rate_stats
    }, indent=2)


# ============================================================================
# PHASE 4: Analysis Tools
# ============================================================================

@mcp.tool()
async def gemini_summarize(
    content: str,
    focus: Optional[str] = None,
    model: Optional[str] = None
) -> str:
    """
    Summarize content with focus-specific analysis (400,000 char limit).

    Args:
        content: Content to summarize (supports @filename syntax)
        focus: Optional focus area (e.g., "architecture and design patterns")
        model: Optional model to use

    Returns:
        JSON string with summarization results

    Examples:
        gemini_summarize(content="@src/ @tests/", focus="architecture")
    """
    model = model or "gemini-2.5-pro"
    scaling_factor = get_model_scaling_factor(model)
    effective_limit = int(GEMINI_SUMMARIZE_LIMIT * scaling_factor)

    if len(content) > effective_limit:
        return json.dumps({
            "status": "error",
            "error": f"Content exceeds limit of {effective_limit:,} characters",
            "error_code": "INPUT_TOO_LARGE"
        })

    # Build prompt using template
    try:
        from prompts.summarize_template import get_summarize_prompt
        prompt = get_summarize_prompt(content, focus)
    except ImportError:
        # Fallback prompt
        focus_text = f" Focus on: {focus}" if focus else ""
        prompt = f"Please summarize the following content.{focus_text}\n\n{content}"

    args = ["--model", model, "--prompt", prompt]

    try:
        result = await execute_gemini_with_retry(args, fallback_model=FALLBACK_MODEL)
        return json.dumps(result, indent=2)
    except (GeminiTimeoutError, GeminiRateLimitError, GeminiExecutionError) as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        })


@mcp.tool()
async def gemini_summarize_files(
    files: str,
    focus: Optional[str] = None,
    model: Optional[str] = None
) -> str:
    """
    File-based summarization optimized for @filename syntax (800,000 char limit).

    Args:
        files: Files to summarize using @filename syntax (e.g., "@src/ @docs/")
        focus: Optional focus area for analysis
        model: Optional model to use

    Returns:
        JSON string with summarization results

    Examples:
        gemini_summarize_files(files="@src/ @docs/ @tests/", focus="complete system analysis")
    """
    model = model or "gemini-2.5-pro"
    scaling_factor = get_model_scaling_factor(model)
    effective_limit = int(GEMINI_SUMMARIZE_FILES_LIMIT * scaling_factor)

    if len(files) > effective_limit:
        return json.dumps({
            "status": "error",
            "error": f"Files specification exceeds limit of {effective_limit:,} characters",
            "error_code": "INPUT_TOO_LARGE"
        })

    # Build lightweight prompt for file analysis
    focus_text = f" Focus on: {focus}" if focus else ""
    prompt = f"Analyze and summarize the following files.{focus_text}\n\n{files}"

    args = ["--model", model, "--prompt", prompt]

    try:
        result = await execute_gemini_with_retry(args, fallback_model=FALLBACK_MODEL)
        return json.dumps(result, indent=2)
    except (GeminiTimeoutError, GeminiRateLimitError, GeminiExecutionError) as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        })


@mcp.tool()
async def gemini_eval_plan(
    plan: str,
    context: Optional[str] = None,
    requirements: Optional[str] = None,
    model: Optional[str] = None
) -> str:
    """
    Evaluate Claude Code implementation plans (500,000 char limit).

    Args:
        plan: The implementation plan to evaluate
        context: Optional context (e.g., "Node.js REST API with MongoDB")
        requirements: Optional requirements (e.g., "Must support 10,000 concurrent users")
        model: Optional model to use

    Returns:
        JSON string with evaluation results

    Examples:
        gemini_eval_plan(plan="1. Create JWT auth...", context="Express.js API")
    """
    model = model or "gemini-2.5-pro"
    scaling_factor = get_model_scaling_factor(model)
    effective_limit = int(GEMINI_EVAL_LIMIT * scaling_factor)

    total_length = len(plan) + len(context or "") + len(requirements or "")
    if total_length > effective_limit:
        return json.dumps({
            "status": "error",
            "error": f"Input exceeds limit of {effective_limit:,} characters",
            "error_code": "INPUT_TOO_LARGE"
        })

    try:
        from prompts.eval_template import get_eval_plan_prompt
        prompt = get_eval_plan_prompt(plan, context, requirements)
    except ImportError:
        # Fallback prompt
        context_text = f"\n\nContext: {context}" if context else ""
        req_text = f"\n\nRequirements: {requirements}" if requirements else ""
        prompt = f"""Please evaluate the following implementation plan for completeness,
correctness, and potential issues.{context_text}{req_text}

Plan:
{plan}

Provide a detailed analysis with:
1. Strengths
2. Potential issues
3. Missing considerations
4. Recommendations"""

    args = ["--model", model, "--prompt", prompt]

    try:
        result = await execute_gemini_with_retry(args, fallback_model=FALLBACK_MODEL)
        return json.dumps(result, indent=2)
    except (GeminiTimeoutError, GeminiRateLimitError, GeminiExecutionError) as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        })


@mcp.tool()
async def gemini_review_code(
    code: str,
    purpose: Optional[str] = None,
    context: Optional[str] = None,
    language: Optional[str] = None,
    model: Optional[str] = None
) -> str:
    """
    Review specific code suggestions with detailed analysis (300,000 char limit).

    Args:
        code: Code to review (supports @filename syntax)
        purpose: Purpose of the review (e.g., "Security review")
        context: Additional context
        language: Programming language
        model: Optional model to use

    Returns:
        JSON string with review results

    Examples:
        gemini_review_code(code="@src/auth.py", purpose="Security review", language="python")
    """
    model = model or "gemini-2.5-pro"
    scaling_factor = get_model_scaling_factor(model)
    effective_limit = int(GEMINI_REVIEW_LIMIT * scaling_factor)

    total_length = len(code) + len(purpose or "") + len(context or "")
    if total_length > effective_limit:
        return json.dumps({
            "status": "error",
            "error": f"Input exceeds limit of {effective_limit:,} characters",
            "error_code": "INPUT_TOO_LARGE"
        })

    try:
        from prompts.review_template import get_review_code_prompt
        prompt = get_review_code_prompt(code, purpose, context, language)
    except ImportError:
        # Fallback prompt
        purpose_text = f"\n\nPurpose: {purpose}" if purpose else ""
        context_text = f"\n\nContext: {context}" if context else ""
        lang_text = f"\n\nLanguage: {language}" if language else ""
        prompt = f"""Please review the following code.{purpose_text}{context_text}{lang_text}

Code:
{code}

Provide a detailed review covering:
1. Code quality
2. Potential bugs
3. Security concerns
4. Performance considerations
5. Recommendations"""

    args = ["--model", model, "--prompt", prompt]

    try:
        result = await execute_gemini_with_retry(args, fallback_model=FALLBACK_MODEL)
        return json.dumps(result, indent=2)
    except (GeminiTimeoutError, GeminiRateLimitError, GeminiExecutionError) as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        })


@mcp.tool()
async def gemini_verify_solution(
    solution: str,
    requirements: Optional[str] = None,
    test_criteria: Optional[str] = None,
    context: Optional[str] = None,
    model: Optional[str] = None
) -> str:
    """
    Comprehensive verification of complete solutions (800,000 char limit).

    Args:
        solution: Complete solution to verify
        requirements: Original requirements
        test_criteria: Testing and performance criteria
        context: Deployment context
        model: Optional model to use

    Returns:
        JSON string with verification results

    Examples:
        gemini_verify_solution(solution="...", requirements="Auth system", test_criteria="99.9% uptime")
    """
    model = model or "gemini-2.5-pro"
    scaling_factor = get_model_scaling_factor(model)
    effective_limit = int(GEMINI_VERIFY_LIMIT * scaling_factor)

    total_length = (len(solution) + len(requirements or "") +
                    len(test_criteria or "") + len(context or ""))
    if total_length > effective_limit:
        return json.dumps({
            "status": "error",
            "error": f"Input exceeds limit of {effective_limit:,} characters",
            "error_code": "INPUT_TOO_LARGE"
        })

    try:
        from prompts.verify_template import get_verify_solution_prompt
        prompt = get_verify_solution_prompt(solution, requirements, test_criteria, context)
    except ImportError:
        # Fallback prompt
        req_text = f"\n\nRequirements: {requirements}" if requirements else ""
        test_text = f"\n\nTest Criteria: {test_criteria}" if test_criteria else ""
        ctx_text = f"\n\nContext: {context}" if context else ""
        prompt = f"""Please verify the following solution comprehensively.{req_text}{test_text}{ctx_text}

Solution:
{solution}

Verify:
1. Completeness against requirements
2. Code correctness
3. Security considerations
4. Performance implications
5. Test coverage adequacy
6. Production readiness"""

    args = ["--model", model, "--prompt", prompt]

    try:
        result = await execute_gemini_with_retry(args, fallback_model=FALLBACK_MODEL)
        return json.dumps(result, indent=2)
    except (GeminiTimeoutError, GeminiRateLimitError, GeminiExecutionError) as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        })


# ============================================================================
# PHASE 5: Conversation Management
# ============================================================================

@mcp.tool()
async def gemini_start_conversation(
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
    expiration_hours: int = 24
) -> str:
    """
    Start a new conversation with ID for stateful interactions.

    Args:
        title: Optional title for the conversation
        description: Optional description
        tags: Optional comma-separated tags
        expiration_hours: Hours until conversation expires (default: 24)

    Returns:
        JSON with conversation_id and details

    Examples:
        gemini_start_conversation(title="Python Help", tags="python,development")
    """
    try:
        from modules.services.conversation_manager import ConversationManager
        manager = ConversationManager()
        conversation = manager.create_conversation(
            title=title,
            description=description,
            tags=tags.split(",") if tags else None,
            expiration_hours=expiration_hours
        )
        return json.dumps({
            "status": "success",
            "conversation": conversation
        }, indent=2)
    except ImportError:
        # Fallback implementation
        import uuid
        conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
        return json.dumps({
            "status": "success",
            "conversation": {
                "conversation_id": conversation_id,
                "title": title,
                "description": description,
                "tags": tags.split(",") if tags else [],
                "created_at": __import__("time").time(),
                "expiration_hours": expiration_hours,
                "message_count": 0
            }
        }, indent=2)


@mcp.tool()
async def gemini_continue_conversation(
    conversation_id: str,
    prompt: str,
    model: Optional[str] = None
) -> str:
    """
    Continue an existing conversation with context history.

    Args:
        conversation_id: ID of the conversation to continue
        prompt: The new prompt/message
        model: Optional model to use

    Returns:
        JSON with response and updated conversation state

    Examples:
        gemini_continue_conversation(conversation_id="conv_12345", prompt="How do I optimize this?")
    """
    model = model or DEFAULT_MODEL

    try:
        from modules.services.conversation_manager import ConversationManager
        manager = ConversationManager()
        result = await manager.continue_conversation(
            conversation_id=conversation_id,
            prompt=prompt,
            model=model
        )
        return json.dumps(result, indent=2)
    except ImportError:
        # Fallback - just execute prompt without history
        args = ["--model", model, "--prompt", prompt]
        result = await execute_gemini_with_retry(args, fallback_model=FALLBACK_MODEL)
        return json.dumps({
            "status": "success",
            "conversation_id": conversation_id,
            "response": result
        }, indent=2)


@mcp.tool()
async def gemini_list_conversations(
    limit: int = 20,
    status_filter: Optional[str] = None
) -> str:
    """
    List active conversations with metadata.

    Args:
        limit: Maximum number of conversations to return
        status_filter: Optional filter (active, expired)

    Returns:
        JSON with list of conversations

    Examples:
        gemini_list_conversations(limit=10, status_filter="active")
    """
    try:
        from modules.services.conversation_manager import ConversationManager
        manager = ConversationManager()
        conversations = manager.list_conversations(
            limit=limit,
            status_filter=status_filter
        )
        return json.dumps({
            "status": "success",
            "conversations": conversations,
            "total": len(conversations)
        }, indent=2)
    except ImportError:
        return json.dumps({
            "status": "success",
            "conversations": [],
            "total": 0,
            "note": "Conversation management not fully configured"
        }, indent=2)


@mcp.tool()
async def gemini_clear_conversation(conversation_id: str) -> str:
    """
    Clear/delete a specific conversation.

    Args:
        conversation_id: ID of the conversation to clear

    Returns:
        JSON with confirmation

    Examples:
        gemini_clear_conversation(conversation_id="conv_12345")
    """
    try:
        from modules.services.conversation_manager import ConversationManager
        manager = ConversationManager()
        result = manager.clear_conversation(conversation_id)
        return json.dumps(result, indent=2)
    except ImportError:
        return json.dumps({
            "status": "success",
            "message": f"Conversation {conversation_id} cleared",
            "note": "Conversation management not fully configured"
        }, indent=2)


@mcp.tool()
async def gemini_conversation_stats() -> str:
    """
    Get conversation system statistics and health.

    Returns:
        JSON with conversation system statistics

    Examples:
        gemini_conversation_stats()
    """
    try:
        from modules.services.conversation_manager import ConversationManager
        manager = ConversationManager()
        stats = manager.get_stats()
        return json.dumps({
            "status": "success",
            "statistics": stats
        }, indent=2)
    except ImportError:
        return json.dumps({
            "status": "success",
            "statistics": {
                "active_conversations": 0,
                "total_messages": 0,
                "storage_backend": "not_configured"
            }
        }, indent=2)


# ============================================================================
# PHASE 6: Specialized Code Review Tools
# ============================================================================

@mcp.tool()
async def gemini_code_review(
    code: str,
    language: Optional[str] = None,
    focus_areas: Optional[str] = None,
    severity_threshold: str = "info",
    output_format: str = "structured"
) -> str:
    """
    Comprehensive code analysis with structured output (300,000 char limit).

    Args:
        code: Code to review
        language: Programming language (auto-detected if not specified)
        focus_areas: Comma-separated focus areas (security,performance,quality,best_practices)
        severity_threshold: Minimum severity to report (info, warning, error, critical)
        output_format: Output format (structured, markdown, json)

    Returns:
        JSON with structured code review

    Examples:
        gemini_code_review(code="@src/api/", focus_areas="security,performance")
    """
    try:
        from modules.core.mcp_code_review_tools import execute_code_review
        return await execute_code_review(
            code=code,
            language=language,
            focus_areas=focus_areas,
            severity_threshold=severity_threshold,
            output_format=output_format
        )
    except ImportError:
        # Fallback implementation
        model = "gemini-2.5-pro"
        focus_text = f"\n\nFocus areas: {focus_areas}" if focus_areas else ""
        lang_text = f"\n\nLanguage: {language}" if language else ""
        prompt = f"""Perform a comprehensive code review.{focus_text}{lang_text}

Code:
{code}

Provide analysis in {output_format} format with severity levels."""

        args = ["--model", model, "--prompt", prompt]
        result = await execute_gemini_with_retry(args)
        return json.dumps(result, indent=2)


@mcp.tool()
async def gemini_extract_structured(
    content: str,
    schema: str,
    examples: Optional[str] = None,
    strict_mode: bool = True,
    model: Optional[str] = None
) -> str:
    """
    Extract structured data using JSON schemas (200,000 char limit).

    Args:
        content: Content to analyze
        schema: JSON schema defining the output structure
        examples: Optional examples of expected output
        strict_mode: Whether to enforce strict schema compliance
        model: Optional model to use

    Returns:
        JSON with extracted structured data

    Examples:
        gemini_extract_structured(content="@src/", schema='{"type":"object",...}')
    """
    try:
        from modules.core.mcp_code_review_tools import execute_extract_structured
        return await execute_extract_structured(
            content=content,
            schema=schema,
            examples=examples,
            strict_mode=strict_mode,
            model=model
        )
    except ImportError:
        # Fallback implementation
        model = model or "gemini-2.5-flash"
        strict_text = " Strictly follow the schema." if strict_mode else ""
        example_text = f"\n\nExamples:\n{examples}" if examples else ""
        prompt = f"""Extract structured data from the following content according to this schema.{strict_text}

Schema:
{schema}{example_text}

Content:
{content}

Return valid JSON matching the schema."""

        args = ["--model", model, "--prompt", prompt]
        result = await execute_gemini_with_retry(args)
        return json.dumps(result, indent=2)


@mcp.tool()
async def gemini_git_diff_review(
    diff: str,
    context_lines: int = 3,
    review_type: str = "comprehensive",
    base_branch: Optional[str] = None,
    commit_message: Optional[str] = None
) -> str:
    """
    Analyze git diffs with contextual feedback (150,000 char limit).

    Args:
        diff: Git diff content or patch
        context_lines: Number of context lines around changes
        review_type: Review type (comprehensive, security_only, performance_only, quick)
        base_branch: Base branch for context
        commit_message: Associated commit message

    Returns:
        JSON with diff analysis

    Examples:
        gemini_git_diff_review(diff="@pull_request.diff", review_type="security_only")
    """
    try:
        from modules.core.mcp_code_review_tools import execute_git_diff_review
        return await execute_git_diff_review(
            diff=diff,
            context_lines=context_lines,
            review_type=review_type,
            base_branch=base_branch,
            commit_message=commit_message
        )
    except ImportError:
        # Fallback implementation
        model = "gemini-2.5-pro"
        branch_text = f"\n\nBase branch: {base_branch}" if base_branch else ""
        commit_text = f"\n\nCommit message: {commit_message}" if commit_message else ""
        prompt = f"""Review the following git diff ({review_type} review).{branch_text}{commit_text}

Diff:
{diff}

Provide feedback on:
1. Code quality changes
2. Potential issues introduced
3. Security implications
4. Suggestions for improvement"""

        args = ["--model", model, "--prompt", prompt]
        result = await execute_gemini_with_retry(args)
        return json.dumps(result, indent=2)


# ============================================================================
# PHASE 7: Content Comparison
# ============================================================================

@mcp.tool()
async def gemini_content_comparison(
    sources: str,
    comparison_type: str = "semantic",
    output_format: str = "structured",
    include_metrics: bool = True,
    focus_areas: Optional[str] = None
) -> str:
    """
    Advanced multi-source content comparison and analysis (400,000 char limit).

    Args:
        sources: JSON array of sources to compare (supports @filename and URLs)
        comparison_type: Type of comparison (semantic, textual, structural, factual, code)
        output_format: Output format (structured, matrix, summary, detailed, json)
        include_metrics: Include similarity scores and metrics
        focus_areas: Comma-separated focus areas

    Returns:
        JSON with comparison results

    Examples:
        gemini_content_comparison(sources='["@README.md", "@docs/README.md"]', comparison_type="semantic")
    """
    try:
        from modules.core.mcp_content_comparison_tools import execute_content_comparison
        return await execute_content_comparison(
            sources=sources,
            comparison_type=comparison_type,
            output_format=output_format,
            include_metrics=include_metrics,
            focus_areas=focus_areas
        )
    except ImportError:
        # Fallback implementation
        model = "gemini-2.5-pro"
        focus_text = f"\n\nFocus on: {focus_areas}" if focus_areas else ""
        prompt = f"""Compare the following sources using {comparison_type} comparison.{focus_text}

Sources:
{sources}

Provide a {output_format} comparison{"with similarity metrics" if include_metrics else ""}."""

        args = ["--model", model, "--prompt", prompt]
        result = await execute_gemini_with_retry(args)
        return json.dumps(result, indent=2)


# ============================================================================
# PHASE 8: OpenRouter Integration
# ============================================================================

@mcp.tool()
async def gemini_test_openrouter() -> str:
    """
    Test OpenRouter connectivity and client functionality.

    Returns:
        JSON with test results

    Examples:
        gemini_test_openrouter()
    """
    try:
        from modules.services.openrouter_client import OpenRouterClient
        client = OpenRouterClient()
        result = await client.test_connection()
        return json.dumps({
            "status": "success",
            "test_results": result
        }, indent=2)
    except ImportError:
        return json.dumps({
            "status": "error",
            "error": "OpenRouter client not configured",
            "hint": "Set OPENROUTER_API_KEY environment variable"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)


@mcp.tool()
async def gemini_openrouter_opinion(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    file_handling_strategy: str = "auto"
) -> str:
    """
    Get responses from any of 400+ AI models via OpenRouter (150,000 char limit).

    Args:
        prompt: The prompt (supports @filename syntax)
        model: OpenRouter model ID (e.g., "anthropic/claude-3-haiku")
        temperature: Sampling temperature (0.0-2.0)
        max_tokens: Maximum tokens in response
        file_handling_strategy: Strategy for large files (auto, full, chunk, summarize)

    Returns:
        JSON with model response

    Examples:
        gemini_openrouter_opinion(prompt="Analyze @config.yaml", model="anthropic/claude-3-haiku")
    """
    try:
        from modules.services.openrouter_client import OpenRouterClient
        client = OpenRouterClient()
        result = await client.get_opinion(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            file_handling_strategy=file_handling_strategy
        )
        return json.dumps(result, indent=2)
    except ImportError:
        return json.dumps({
            "status": "error",
            "error": "OpenRouter client not configured",
            "hint": "Set OPENROUTER_API_KEY environment variable"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)


@mcp.tool()
async def gemini_openrouter_models(
    category: Optional[str] = None,
    provider_filter: Optional[str] = None,
    sort_by: str = "usage",
    include_pricing: bool = True
) -> str:
    """
    List all available OpenRouter models (400+).

    Args:
        category: Filter by category (programming, creative, general, etc.)
        provider_filter: Filter by provider (openai, anthropic, meta, etc.)
        sort_by: Sort order (usage, price, name, context_length)
        include_pricing: Include pricing information

    Returns:
        JSON with model list

    Examples:
        gemini_openrouter_models(provider_filter="openai", include_pricing=True)
    """
    try:
        from modules.services.openrouter_client import OpenRouterClient
        client = OpenRouterClient()
        result = await client.list_models(
            category=category,
            provider_filter=provider_filter,
            sort_by=sort_by,
            include_pricing=include_pricing
        )
        return json.dumps(result, indent=2)
    except ImportError:
        return json.dumps({
            "status": "error",
            "error": "OpenRouter client not configured"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)


@mcp.tool()
async def gemini_cross_model_comparison(
    prompt: str,
    models: str = "gemini-2.5-flash,openai/gpt-4.1-mini,anthropic/claude-3-haiku"
) -> str:
    """
    Compare responses across Gemini CLI and OpenRouter models.

    Args:
        prompt: The prompt to send to all models
        models: Comma-separated list of models

    Returns:
        JSON with comparison results

    Examples:
        gemini_cross_model_comparison(prompt="Design a REST API", models="gemini-2.5-flash,openai/gpt-4.1-mini")
    """
    model_list = [m.strip() for m in models.split(",")]
    results = {}

    for model in model_list:
        try:
            if model.startswith("gemini"):
                # Use Gemini CLI
                args = ["--model", model, "--prompt", prompt]
                result = await execute_gemini_with_retry(args)
                results[model] = {
                    "status": "success",
                    "response": result.get("stdout", ""),
                    "source": "gemini_cli"
                }
            else:
                # Use OpenRouter
                try:
                    from modules.services.openrouter_client import OpenRouterClient
                    client = OpenRouterClient()
                    result = await client.get_opinion(prompt=prompt, model=model)
                    results[model] = {
                        "status": "success",
                        "response": result.get("content", ""),
                        "source": "openrouter"
                    }
                except ImportError:
                    results[model] = {
                        "status": "error",
                        "error": "OpenRouter not configured"
                    }
        except Exception as e:
            results[model] = {
                "status": "error",
                "error": str(e)
            }

    return json.dumps({
        "status": "success",
        "prompt": prompt[:500] + "..." if len(prompt) > 500 else prompt,
        "comparisons": results
    }, indent=2)


@mcp.tool()
async def gemini_openrouter_usage_stats() -> str:
    """
    Get OpenRouter usage statistics and costs for the current session.

    Returns:
        JSON with usage statistics

    Examples:
        gemini_openrouter_usage_stats()
    """
    try:
        from modules.services.openrouter_client import OpenRouterClient
        client = OpenRouterClient()
        stats = client.get_usage_stats()
        return json.dumps({
            "status": "success",
            "usage_statistics": stats
        }, indent=2)
    except ImportError:
        return json.dumps({
            "status": "success",
            "usage_statistics": {
                "total_requests": 0,
                "total_cost": 0.0,
                "note": "OpenRouter not configured"
            }
        }, indent=2)


# ============================================================================
# PHASE 9: AI Collaboration Engine
# ============================================================================

@mcp.tool()
async def gemini_ai_collaboration(
    collaboration_mode: str,
    content: str,
    models: Optional[str] = None,
    context: Optional[str] = None,
    conversation_id: Optional[str] = None,
    budget_limit: Optional[float] = None,
    # Sequential mode params
    pipeline_stages: Optional[str] = None,
    handoff_criteria: str = "completion_of_stage",
    quality_gates: str = "standard",
    # Debate mode params
    rounds: int = 3,
    debate_style: str = "constructive",
    convergence_criteria: str = "substantial_agreement",
    # Validation mode params
    validation_criteria: Optional[str] = None,
    confidence_threshold: float = 0.7,
    consensus_method: str = "weighted_majority",
    conflict_resolution: str = "detailed_analysis",
    focus: Optional[str] = None
) -> str:
    """
    Enhanced multi-platform AI collaboration (500,000 char limit).

    Args:
        collaboration_mode: Mode (sequential, debate, validation)
        content: Content to analyze
        models: Comma-separated model list
        context: Additional context
        conversation_id: For stateful conversations
        budget_limit: USD cost limit for OpenRouter
        pipeline_stages: Stages for sequential mode
        handoff_criteria: Handoff criteria for sequential
        quality_gates: Quality gates for sequential
        rounds: Number of debate rounds
        debate_style: Style for debate mode
        convergence_criteria: When debate converges
        validation_criteria: Criteria for validation mode
        confidence_threshold: Confidence threshold for validation
        consensus_method: How to reach consensus
        conflict_resolution: How to resolve conflicts
        focus: Focus area

    Returns:
        JSON with collaboration results

    Examples:
        gemini_ai_collaboration(collaboration_mode="debate", content="Microservices vs monolith?", rounds=3)
    """
    try:
        from modules.core.mcp_collaboration_engine import execute_collaboration
        return await execute_collaboration(
            collaboration_mode=collaboration_mode,
            content=content,
            models=models,
            context=context,
            conversation_id=conversation_id,
            budget_limit=budget_limit,
            pipeline_stages=pipeline_stages,
            handoff_criteria=handoff_criteria,
            quality_gates=quality_gates,
            rounds=rounds,
            debate_style=debate_style,
            convergence_criteria=convergence_criteria,
            validation_criteria=validation_criteria,
            confidence_threshold=confidence_threshold,
            consensus_method=consensus_method,
            conflict_resolution=conflict_resolution,
            focus=focus
        )
    except ImportError:
        # Fallback - simplified collaboration
        model_list = (models or "gemini-2.5-flash").split(",")
        results = []

        for model in model_list:
            model = model.strip()
            mode_prompt = {
                "sequential": f"Analyze the following content:\n\n{content}",
                "debate": f"Provide your perspective on:\n\n{content}",
                "validation": f"Validate the following:\n\n{content}"
            }.get(collaboration_mode, content)

            if model.startswith("gemini"):
                args = ["--model", model, "--prompt", mode_prompt]
                try:
                    result = await execute_gemini_with_retry(args)
                    results.append({
                        "model": model,
                        "response": result.get("stdout", "")
                    })
                except Exception as e:
                    results.append({"model": model, "error": str(e)})

        return json.dumps({
            "status": "success",
            "collaboration_mode": collaboration_mode,
            "results": results
        }, indent=2)


# ============================================================================
# Server Entry Point
# ============================================================================

def main():
    """Run the MCP server."""
    logger.info("Starting Gemini CLI MCP Server")
    logger.info(f"Log level: {log_level}")

    if validate_gemini_setup():
        logger.info("Gemini CLI setup validated successfully")
    else:
        logger.warning("Gemini CLI not found - some features may not work")

    mcp.run()


if __name__ == "__main__":
    main()
