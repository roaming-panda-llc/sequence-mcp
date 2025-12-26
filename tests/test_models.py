"""Tests for Pydantic models."""

import pytest

from sequence_mcp.models import (
    Account,
    AccountBalance,
    AccountsResponse,
    TriggerRuleResponse,
    SequenceError,
)


def describe_AccountBalance():
    """Tests for AccountBalance model."""

    def it_parses_balance_with_alias():
        data = {"amountInDollars": 1234.56, "error": None}
        balance = AccountBalance.model_validate(data)
        assert balance.amount_in_dollars == 1234.56
        assert balance.error is None

    def it_handles_null_balance_with_error():
        data = {"amountInDollars": None, "error": "Connection timeout"}
        balance = AccountBalance.model_validate(data)
        assert balance.amount_in_dollars is None
        assert balance.error == "Connection timeout"


def describe_Account():
    """Tests for Account model."""

    def it_parses_pod_account():
        data = {
            "id": "123",
            "name": "Savings Pod",
            "balance": {"amountInDollars": 5000.00, "error": None},
            "type": "Pod",
        }
        account = Account.model_validate(data)
        assert account.id == "123"
        assert account.name == "Savings Pod"
        assert account.type == "Pod"
        assert account.balance.amount_in_dollars == 5000.00

    def it_parses_income_source_account():
        data = {
            "id": "456",
            "name": "Client Payments",
            "balance": {"amountInDollars": 10000.00, "error": None},
            "type": "Income Source",
        }
        account = Account.model_validate(data)
        assert account.type == "Income Source"

    def it_parses_external_account():
        data = {
            "id": "external_789",
            "name": "Chase Checking",
            "balance": {"amountInDollars": 2500.00, "error": None},
            "type": "Account",
        }
        account = Account.model_validate(data)
        assert account.type == "Account"


def describe_AccountsResponse():
    """Tests for AccountsResponse model."""

    def it_parses_full_response():
        data = {
            "message": "OK",
            "requestId": "req-123",
            "data": {
                "accounts": [
                    {
                        "id": "1",
                        "name": "Test",
                        "balance": {"amountInDollars": 100.0, "error": None},
                        "type": "Pod",
                    }
                ],
                "errors": [],
            },
        }
        response = AccountsResponse.model_validate(data)
        assert response.message == "OK"
        assert response.request_id == "req-123"
        assert len(response.data.accounts) == 1

    def it_handles_response_with_errors():
        data = {
            "message": "OK",
            "requestId": "req-456",
            "data": {
                "accounts": [],
                "errors": ["Failed to fetch external account"],
            },
        }
        response = AccountsResponse.model_validate(data)
        assert len(response.data.errors) == 1
        assert "external account" in response.data.errors[0]


def describe_TriggerRuleResponse():
    """Tests for TriggerRuleResponse model."""

    def it_parses_successful_response():
        data = {
            "code": "OK",
            "message": "Rule with id ru_123 has been triggered",
            "data": {"requestId": "req-xyz"},
        }
        response = TriggerRuleResponse.model_validate(data)
        assert response.code == "OK"
        assert response.message == "Rule with id ru_123 has been triggered"
        assert response.data.request_id == "req-xyz"


def describe_SequenceError():
    """Tests for SequenceError exception."""

    def it_stores_error_details():
        error = SequenceError(
            code="INVALID_REQUEST",
            message="Rule not found",
            status_code=400,
        )
        assert error.code == "INVALID_REQUEST"
        assert error.message == "Rule not found"
        assert error.status_code == 400

    def it_formats_string_representation():
        error = SequenceError(
            code="UNAUTHORIZED",
            message="Invalid token",
        )
        assert str(error) == "UNAUTHORIZED: Invalid token"

    def it_can_be_raised_and_caught():
        with pytest.raises(SequenceError) as exc_info:
            raise SequenceError(code="TEST", message="test error")
        assert exc_info.value.code == "TEST"
