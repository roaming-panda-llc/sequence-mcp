# Sequence Banking MCP Server

An MCP (Model Context Protocol) server that provides access to the [Sequence](https://getsequence.io) banking API. This allows AI assistants like Claude to interact with your Sequence accounts programmatically.

## Features

- **Get Accounts**: Fetch all financial accounts (Pods, Income Sources, external accounts) with current balances
- **Trigger Rules**: Invoke automation rules configured in Sequence from external systems

## Requirements

- Python 3.10 or higher
- A Sequence account with the External API enabled
- Access token and/or rule API secrets from your Sequence dashboard

## Installation

1. Clone or download this repository

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the package:
   ```bash
   pip install -e .
   ```

4. For development (includes test dependencies):
   ```bash
   pip install -e ".[dev]"
   ```

## Configuration

### Getting Your Credentials

1. **Enable the External API**: Go to Settings > Enable Remote API in your Sequence dashboard

2. **Generate an Access Token**: Navigate to Account Settings > Access Tokens and create a new token. This is used for fetching account data.

3. **Get Rule API Secrets**: When you create a Rule with "Remote API" trigger type, an API secret is generated. Use this secret to trigger that specific rule.

### Environment Variables

Set your access token as an environment variable:

```bash
export SEQUENCE_ACCESS_TOKEN="your_access_token_here"
```

## Usage

### Running the MCP Server

```bash
source venv/bin/activate
python -m sequence_mcp.server
```

### Using with Claude Desktop

Add the following to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "sequence": {
      "command": "/path/to/sequence-mcp/venv/bin/python",
      "args": ["-m", "sequence_mcp.server"],
      "env": {
        "SEQUENCE_ACCESS_TOKEN": "your_access_token_here"
      }
    }
  }
}
```

Replace `/path/to/sequence-mcp` with the actual path to this project.

### Available Tools

#### get_accounts

Fetches all financial accounts with their current balances.

**Requirements**: `SEQUENCE_ACCESS_TOKEN` environment variable must be set.

**Returns**: List of accounts with id, name, type, and balance information.

#### trigger_rule

Triggers an automation rule in Sequence.

**Parameters**:
- `rule_id` (required): The ID of the rule to trigger (e.g., "ru_12345")
- `api_secret` (required): The API secret associated with this rule
- `payload` (optional): JSON object to send with the trigger
- `idempotency_key` (optional): Unique key to prevent duplicate triggers on retry

## Development

### Running Tests

```bash
source venv/bin/activate
pytest -v
```

### Project Structure

```
sequence-mcp/
├── sequence_mcp/
│   ├── __init__.py      # Package exports
│   ├── models.py        # Pydantic models for API responses
│   ├── client.py        # Async HTTP client for Sequence API
│   └── server.py        # MCP server implementation
├── tests/
│   ├── conftest.py      # Shared test fixtures
│   ├── test_models.py   # Model tests
│   ├── test_client.py   # Client tests
│   └── test_server.py   # Server tests
├── pyproject.toml       # Project configuration
└── README.md
```

## API Reference

This MCP server wraps the Sequence External API. For full API documentation, see:
https://support.getsequence.io/hc/en-us/articles/42813911824019-API-Overview

### Error Codes

| Code | Description |
|------|-------------|
| `INVALID_ACCESS_TOKEN` | Access token is missing or invalid |
| `INVALID_API_SECRET` | Rule API secret is incorrect |
| `INVALID_REQUEST` | Rule ID not found or not configured for API triggers |
| `TOO_MANY_REQUESTS` | Rate limit exceeded, slow down requests |
| `UNEXPECTED_ERROR` | Server error, usually transient |

## Security Notes

- Keep your access tokens and API secrets secure
- Never expose credentials in client-side code
- Use environment variables or secure secret management
- Rotate tokens periodically
- All requests are made over HTTPS

## License

MIT
