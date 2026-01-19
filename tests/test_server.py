"""Tests for the MCP server."""

import json
import os
import pytest
import httpx
import respx

from sequence_mcp.server import (
    list_tools,
    call_tool,
    handle_get_accounts,
    handle_trigger_rule,
)


def describe_list_tools():
    """Tests for listing available tools."""

    @pytest.mark.asyncio
    async def it_returns_two_tools():
        tools = await list_tools()
        assert len(tools) == 2

    @pytest.mark.asyncio
    async def it_includes_get_accounts_tool():
        tools = await list_tools()
        tool_names = [t.name for t in tools]
        assert "get_accounts" in tool_names

    @pytest.mark.asyncio
    async def it_includes_trigger_rule_tool():
        tools = await list_tools()
        tool_names = [t.name for t in tools]
        assert "trigger_rule" in tool_names

    @pytest.mark.asyncio
    async def it_has_correct_schema_for_get_accounts():
        tools = await list_tools()
        get_accounts = next(t for t in tools if t.name == "get_accounts")
        assert get_accounts.inputSchema["type"] == "object"
        assert get_accounts.inputSchema["required"] == []

    @pytest.mark.asyncio
    async def it_has_correct_schema_for_trigger_rule():
        tools = await list_tools()
        trigger_rule = next(t for t in tools if t.name == "trigger_rule")
        assert trigger_rule.inputSchema["type"] == "object"
        assert "rule_id" in trigger_rule.inputSchema["properties"]
        assert "api_secret" in trigger_rule.inputSchema["properties"]
        assert "rule_id" in trigger_rule.inputSchema["required"]
        assert "api_secret" in trigger_rule.inputSchema["required"]


def describe_call_tool():
    """Tests for the call_tool dispatcher."""

    @pytest.mark.asyncio
    async def it_returns_error_for_unknown_tool():
        result = await call_tool("unknown_tool", {})
        assert len(result) == 1
        assert "Unknown tool" in result[0].text

    @pytest.mark.asyncio
    async def it_handles_exceptions_gracefully():
        # Call get_accounts without token set
        original_token = os.environ.get("SEQUENCE_ACCESS_TOKEN")
        if "SEQUENCE_ACCESS_TOKEN" in os.environ:
            del os.environ["SEQUENCE_ACCESS_TOKEN"]

        try:
            result = await call_tool("get_accounts", {})
            data = json.loads(result[0].text)
            assert data["error"] is True
            assert "SEQUENCE_ACCESS_TOKEN" in data["message"]
        finally:
            if original_token:
                os.environ["SEQUENCE_ACCESS_TOKEN"] = original_token

    @pytest.mark.asyncio
    @respx.mock
    async def it_handles_unexpected_exceptions():
        """Test that non-SequenceError exceptions are caught and formatted."""
        # Mock the API to return invalid JSON that will cause a parsing error
        respx.post("https://api.getsequence.io/accounts").mock(
            return_value=httpx.Response(
                200,
                content=b"not valid json",
                headers={"content-type": "application/json"},
            )
        )

        original_token = os.environ.get("SEQUENCE_ACCESS_TOKEN")
        os.environ["SEQUENCE_ACCESS_TOKEN"] = "test_token"

        try:
            result = await call_tool("get_accounts", {})
            data = json.loads(result[0].text)
            assert data["error"] is True
            # The error message should contain something about JSON parsing
            assert "message" in data
        finally:
            if original_token:
                os.environ["SEQUENCE_ACCESS_TOKEN"] = original_token
            else:
                del os.environ["SEQUENCE_ACCESS_TOKEN"]


def describe_handle_get_accounts():
    """Tests for the get_accounts handler."""

    @pytest.mark.asyncio
    async def it_returns_error_when_token_not_set():
        original_token = os.environ.get("SEQUENCE_ACCESS_TOKEN")
        if "SEQUENCE_ACCESS_TOKEN" in os.environ:
            del os.environ["SEQUENCE_ACCESS_TOKEN"]

        try:
            result = await handle_get_accounts()
            data = json.loads(result[0].text)
            assert data["error"] is True
            assert "SEQUENCE_ACCESS_TOKEN" in data["message"]
        finally:
            if original_token:
                os.environ["SEQUENCE_ACCESS_TOKEN"] = original_token

    @pytest.mark.asyncio
    @respx.mock
    async def it_returns_accounts_when_successful(sample_accounts_response):
        respx.post("https://api.getsequence.io/accounts").mock(
            return_value=httpx.Response(200, json=sample_accounts_response)
        )

        original_token = os.environ.get("SEQUENCE_ACCESS_TOKEN")
        os.environ["SEQUENCE_ACCESS_TOKEN"] = "test_token"

        try:
            result = await handle_get_accounts()
            data = json.loads(result[0].text)
            assert "accounts" in data
            assert data["total_accounts"] == 3
            assert data["accounts"][0]["name"] == "Main Operating Pod"
            assert data["accounts"][0]["balance_dollars"] == 25342.77
        finally:
            if original_token:
                os.environ["SEQUENCE_ACCESS_TOKEN"] = original_token
            else:
                del os.environ["SEQUENCE_ACCESS_TOKEN"]

    @pytest.mark.asyncio
    @respx.mock
    async def it_handles_api_errors(sample_error_response_unauthorized):
        respx.post("https://api.getsequence.io/accounts").mock(
            return_value=httpx.Response(401, json=sample_error_response_unauthorized)
        )

        original_token = os.environ.get("SEQUENCE_ACCESS_TOKEN")
        os.environ["SEQUENCE_ACCESS_TOKEN"] = "invalid_token"

        try:
            result = await call_tool("get_accounts", {})
            data = json.loads(result[0].text)
            assert data["error"] is True
            assert data["code"] == "INVALID_ACCESS_TOKEN"
        finally:
            if original_token:
                os.environ["SEQUENCE_ACCESS_TOKEN"] = original_token
            else:
                del os.environ["SEQUENCE_ACCESS_TOKEN"]


def describe_handle_trigger_rule():
    """Tests for the trigger_rule handler."""

    @pytest.mark.asyncio
    async def it_returns_error_when_rule_id_missing():
        result = await handle_trigger_rule({"api_secret": "secret"})
        data = json.loads(result[0].text)
        assert data["error"] is True
        assert "rule_id" in data["message"]

    @pytest.mark.asyncio
    async def it_returns_error_when_api_secret_missing():
        result = await handle_trigger_rule({"rule_id": "ru_123"})
        data = json.loads(result[0].text)
        assert data["error"] is True
        assert "api_secret" in data["message"]

    @pytest.mark.asyncio
    @respx.mock
    async def it_triggers_rule_successfully(sample_trigger_response):
        respx.post(
            "https://api.getsequence.io/remote-api/rules/ru_12345/trigger"
        ).mock(return_value=httpx.Response(200, json=sample_trigger_response))

        result = await handle_trigger_rule(
            {"rule_id": "ru_12345", "api_secret": "secret_123"}
        )
        data = json.loads(result[0].text)

        assert data["success"] is True
        assert data["code"] == "OK"
        assert data["request_id"] == "b28f1d9e-8c2a-4d3e-9af1-XXXXXXXXXXXX"

    @pytest.mark.asyncio
    @respx.mock
    async def it_passes_payload_to_api(sample_trigger_response):
        route = respx.post(
            "https://api.getsequence.io/remote-api/rules/ru_test/trigger"
        ).mock(return_value=httpx.Response(200, json=sample_trigger_response))

        await handle_trigger_rule(
            {
                "rule_id": "ru_test",
                "api_secret": "secret",
                "payload": {"custom": "data"},
            }
        )

        request = route.calls[0].request
        body = json.loads(request.content)
        assert body == {"custom": "data"}

    @pytest.mark.asyncio
    @respx.mock
    async def it_passes_idempotency_key_to_api(sample_trigger_response):
        route = respx.post(
            "https://api.getsequence.io/remote-api/rules/ru_test/trigger"
        ).mock(return_value=httpx.Response(200, json=sample_trigger_response))

        await handle_trigger_rule(
            {
                "rule_id": "ru_test",
                "api_secret": "secret",
                "idempotency_key": "my-unique-key",
            }
        )

        request = route.calls[0].request
        assert request.headers["idempotency-key"] == "my-unique-key"

    @pytest.mark.asyncio
    @respx.mock
    async def it_handles_api_errors(sample_error_response_invalid_secret):
        respx.post(
            "https://api.getsequence.io/remote-api/rules/ru_test/trigger"
        ).mock(
            return_value=httpx.Response(401, json=sample_error_response_invalid_secret)
        )

        result = await call_tool(
            "trigger_rule", {"rule_id": "ru_test", "api_secret": "wrong"}
        )
        data = json.loads(result[0].text)

        assert data["error"] is True
        assert data["code"] == "INVALID_API_SECRET"
        assert data["status_code"] == 401
