# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server that wraps the Sequence Banking API, enabling AI assistants to interact with Sequence financial accounts. It provides two tools: `get_accounts` (fetch account balances) and `trigger_rule` (invoke automation rules).

## Development Commands

```bash
# Install dependencies (use dev for testing)
pip install -e ".[dev]"

# Run tests
pytest -v

# Run a single test file
pytest tests/test_client.py -v

# Run a specific test function
pytest tests/test_client.py::describe_SequenceClient::describe_get_accounts::it_fetches_accounts_successfully -v

# Run the MCP server
python -m sequence_mcp.server
```

## Architecture

**Three-layer design:**
1. `models.py` - Pydantic models for API request/response serialization (uses field aliases like `amountInDollars` → `amount_in_dollars`)
2. `client.py` - Async HTTP client (`SequenceClient`) using httpx with context manager support
3. `server.py` - MCP server that exposes tools and delegates to the client

**Authentication:** Two methods coexist:
- Access token (env var `SEQUENCE_ACCESS_TOKEN`) for account operations
- Per-rule API secrets passed as parameters for rule triggers

**Error handling:** `SequenceError` exception carries API error codes (`INVALID_ACCESS_TOKEN`, `INVALID_API_SECRET`, `TOO_MANY_REQUESTS`, etc.) and is converted to JSON error responses by the server.

## Testing

Tests use `pytest-describe` for BDD-style nested test organization. HTTP mocking is done with `respx`. Test files mirror source structure with shared fixtures in `conftest.py`.

Example test pattern:
```python
def describe_ClassName():
    def describe_method_name():
        @pytest.mark.asyncio
        @respx.mock
        async def it_does_something(fixture_name):
            # arrange, act, assert
```
