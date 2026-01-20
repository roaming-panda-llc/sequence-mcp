"""MCP server for the Sequence Banking API."""

import os
import sys
import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .client import SequenceClient
from .models import SequenceError

# Configure logging to stderr so Claude Code can see errors
# (stdout is reserved for MCP protocol messages)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("sequence-mcp")

server = Server("sequence-banking")


def get_access_token() -> str | None:
    """Get the access token from environment."""
    return os.environ.get("SEQUENCE_ACCESS_TOKEN")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_accounts",
            description=(
                "Fetch all financial accounts from Sequence with their current balances. "
                "Returns Pods, Income Sources, and external accounts with balance information. "
                "Requires SEQUENCE_ACCESS_TOKEN environment variable."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="trigger_rule",
            description=(
                "Trigger an automation rule in Sequence. "
                "Rules can automate financial workflows like transfers. "
                "Requires the rule ID and its associated API secret."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "rule_id": {
                        "type": "string",
                        "description": "The ID of the rule to trigger (e.g., 'ru_12345')",
                    },
                    "api_secret": {
                        "type": "string",
                        "description": "The API secret associated with this rule",
                    },
                    "payload": {
                        "type": "object",
                        "description": "Optional JSON payload to send with the trigger",
                        "default": {},
                    },
                    "idempotency_key": {
                        "type": "string",
                        "description": "Optional key to prevent duplicate triggers on retry",
                    },
                },
                "required": ["rule_id", "api_secret"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    logger.info("Tool called: %s with arguments: %s", name, arguments)
    try:
        if name == "get_accounts":
            result = await handle_get_accounts()
        elif name == "trigger_rule":
            result = await handle_trigger_rule(arguments)
        else:
            logger.warning("Unknown tool requested: %s", name)
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        logger.debug("Tool %s completed successfully", name)
        return result
    except SequenceError as e:
        logger.error(
            "SequenceError in %s: code=%s, message=%s, status=%s",
            name,
            e.code,
            e.message,
            e.status_code,
        )
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": True,
                        "code": e.code,
                        "message": e.message,
                        "status_code": e.status_code,
                    }
                ),
            )
        ]
    except Exception as e:
        logger.exception("Unexpected error in tool %s: %s", name, e)
        return [
            TextContent(
                type="text",
                text=json.dumps({"error": True, "message": str(e)}),
            )
        ]


async def handle_get_accounts() -> list[TextContent]:
    """Handle the get_accounts tool call."""
    access_token = get_access_token()
    if not access_token:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": True,
                        "message": "SEQUENCE_ACCESS_TOKEN environment variable is not set",
                    }
                ),
            )
        ]

    async with SequenceClient(access_token=access_token) as client:
        accounts = await client.get_accounts()

    result = {
        "accounts": [
            {
                "id": account.id,
                "name": account.name,
                "type": account.type,
                "balance_dollars": account.balance.amount_in_dollars,
                "balance_error": account.balance.error,
            }
            for account in accounts
        ],
        "total_accounts": len(accounts),
    }

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def handle_trigger_rule(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle the trigger_rule tool call."""
    rule_id = arguments.get("rule_id")
    api_secret = arguments.get("api_secret")
    payload = arguments.get("payload", {})
    idempotency_key = arguments.get("idempotency_key")

    if not rule_id:
        return [
            TextContent(
                type="text",
                text=json.dumps({"error": True, "message": "rule_id is required"}),
            )
        ]

    if not api_secret:
        return [
            TextContent(
                type="text",
                text=json.dumps({"error": True, "message": "api_secret is required"}),
            )
        ]

    async with SequenceClient() as client:
        response = await client.trigger_rule(
            rule_id=rule_id,
            api_secret=api_secret,
            payload=payload,
            idempotency_key=idempotency_key,
        )

    result = {
        "success": True,
        "code": response.code,
        "message": response.message,
        "request_id": response.data.request_id,
    }

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def main():  # pragma: no cover
    """Run the MCP server."""
    logger.info("Starting Sequence MCP server...")

    # Log environment status (without exposing secrets)
    access_token = get_access_token()
    if access_token:
        logger.info("SEQUENCE_ACCESS_TOKEN is set (%d chars)", len(access_token))
    else:
        logger.warning("SEQUENCE_ACCESS_TOKEN is not set - get_accounts will fail")

    try:
        async with stdio_server() as (read_stream, write_stream):
            logger.info("MCP stdio server started, awaiting requests...")
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
    except Exception as e:
        logger.exception("MCP server error: %s", e)
        raise


if __name__ == "__main__":  # pragma: no cover
    import asyncio

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception("Fatal error starting server: %s", e)
        sys.exit(1)
