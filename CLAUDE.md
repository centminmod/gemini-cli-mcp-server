# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

```bash
# Install dependencies (use uv, recommended)
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt

# Run the MCP server
python mcp_server.py

# Test server imports
python -c "from mcp_server import mcp; print('Server imports OK')"

# Test with MCP inspector (interactive tool testing)
mcp dev mcp_server.py

# Validate Gemini CLI setup
python -c "from modules.utils.gemini_utils import validate_gemini_setup; print(validate_gemini_setup())"
```

## Architecture Overview

This is a **Model Context Protocol (MCP) server** that bridges Google's Gemini CLI with MCP clients (Claude Code, Claude Desktop). It provides 33 specialized tools organized into categories.

### Key Components

| Component | Purpose |
|-----------|---------|
| `mcp_server.py` | Main entry point; registers all 33 MCP tools with FastMCP |
| `modules/core/` | MCP tool implementations (collaboration, code review, content comparison) |
| `modules/config/` | Configuration from environment variables |
| `modules/services/` | External integrations (OpenRouter, Redis, monitoring) |
| `modules/utils/gemini_utils.py` | Core subprocess execution, caching, error handling |
| `prompts/` | AI prompt templates with TTL caching |
| `security/` | Input validation, credential sanitization, attack detection |

### Tool Categories (33 tools total)

1. **Core Gemini Tools** (6): `gemini_cli`, `gemini_help`, `gemini_version`, `gemini_prompt`, `gemini_models`, `gemini_metrics`
2. **System Tools** (3): `gemini_sandbox`, `gemini_cache_stats`, `gemini_rate_limiting_stats`
3. **Analysis Tools** (5): `gemini_summarize`, `gemini_summarize_files`, `gemini_eval_plan`, `gemini_review_code`, `gemini_verify_solution`
4. **Conversation Tools** (5): `gemini_start_conversation`, `gemini_continue_conversation`, `gemini_list_conversations`, `gemini_clear_conversation`, `gemini_conversation_stats`
5. **Code Review Tools** (3): `gemini_code_review`, `gemini_extract_structured`, `gemini_git_diff_review`
6. **Content Comparison** (1): `gemini_content_comparison`
7. **AI Collaboration** (1): `gemini_ai_collaboration`
8. **OpenRouter Tools** (6): `gemini_test_openrouter`, `gemini_openrouter_opinion`, `gemini_openrouter_models`, `gemini_cross_model_comparison`, `gemini_openrouter_usage_stats`

## Key Patterns

### Tool Registration
Tools are registered using the `@mcp.tool()` decorator in `mcp_server.py`. Each tool returns JSON with `status`, `stdout`, `stderr`, `return_code`.

### Async Architecture
All tool functions are `async`. Use `await` for Gemini CLI execution via `execute_gemini_with_retry()`.

### TTL Caching
- Help/version: 30 minutes
- Prompt results: 5 minutes
- Templates: 30 minutes

### @filename Syntax
32 of 33 tools support Gemini CLI's `@filename` syntax for file content. Example: `gemini_prompt(prompt="Analyze @config.py")`.

### Character Limits (tool-specific)
- `gemini_prompt`: 100K
- `gemini_sandbox`: 200K
- `gemini_review_code`: 300K
- `gemini_summarize`: 400K
- `gemini_eval_plan`: 500K
- `gemini_verify_solution`, `gemini_summarize_files`: 800K

## Environment Variables

**Core:**
- `GEMINI_TIMEOUT` - Command timeout in seconds (default: 300)
- `GEMINI_LOG_LEVEL` - DEBUG, INFO, WARNING, ERROR
- `GEMINI_COMMAND_PATH` - Path to gemini CLI executable

**OpenRouter (for 400+ model access):**
- `OPENROUTER_API_KEY` - API key for OpenRouter
- `OPENROUTER_DEFAULT_MODEL` - Default model (e.g., `openai/gpt-4.1-nano`)

**Conversations:**
- `GEMINI_CONVERSATION_STORAGE` - `redis`, `memory`, or `auto`
- `GEMINI_REDIS_HOST`, `GEMINI_REDIS_PORT` - Redis connection

## Dependencies

Core dependencies (in `requirements.txt`):
- `mcp>=0.3.0` - MCP protocol framework
- `httpx>=0.24.0` - Async HTTP client (OpenRouter)
- `cachetools>=5.3.0` - TTL caching
