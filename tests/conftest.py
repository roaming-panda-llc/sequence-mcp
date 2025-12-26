"""Shared test fixtures."""

import pytest


@pytest.fixture
def sample_accounts_response():
    """Sample response from the accounts endpoint."""
    return {
        "message": "OK",
        "requestId": "f1a2b3c4-56d7-890e-fgh1-XXXXXXXXXXXX",
        "data": {
            "accounts": [
                {
                    "id": "5579244",
                    "name": "Main Operating Pod",
                    "balance": {"amountInDollars": 25342.77, "error": None},
                    "type": "Pod",
                },
                {
                    "id": "5579245",
                    "name": "Client Payments Account",
                    "balance": {"amountInDollars": 10200.50, "error": None},
                    "type": "Income Source",
                },
                {
                    "id": "QDBZQjj1lohgeqVWJlnmf5lA4g83ZGCwl3Qx4",
                    "name": "Chase Credit Card",
                    "balance": {"amountInDollars": 137.9, "error": None},
                    "type": "Account",
                },
            ],
            "errors": [],
        },
    }


@pytest.fixture
def sample_trigger_response():
    """Sample response from the trigger rule endpoint."""
    return {
        "code": "OK",
        "message": "Rule with id ru_12345 has been triggered",
        "data": {"requestId": "b28f1d9e-8c2a-4d3e-9af1-XXXXXXXXXXXX"},
    }


@pytest.fixture
def sample_error_response_unauthorized():
    """Sample unauthorized error response."""
    return {"code": "INVALID_ACCESS_TOKEN", "message": "Unauthorized"}


@pytest.fixture
def sample_error_response_invalid_secret():
    """Sample invalid API secret error response."""
    return {"code": "INVALID_API_SECRET", "message": "Unauthorized"}


@pytest.fixture
def sample_error_response_rate_limit():
    """Sample rate limit error response."""
    return {
        "code": "TOO_MANY_REQUESTS",
        "message": "Rule with id ru_12345 has been triggered too many times. Please try again later.",
    }
