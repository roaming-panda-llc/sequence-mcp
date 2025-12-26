"""MCP server for the Sequence Banking API."""

import os
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .client import SequenceClient
from .models import SequenceError


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
    try:
        if name == "get_accounts":
            return await handle_get_accounts()
        elif name == "trigger_rule":
            return await handle_trigger_rule(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except SequenceError as e:
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


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
