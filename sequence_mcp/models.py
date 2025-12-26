"""Pydantic models for Sequence API responses."""

from typing import Literal
from pydantic import BaseModel, Field


class AccountBalance(BaseModel):
    """Balance information for an account."""

    amount_in_dollars: float | None = Field(
        alias="amountInDollars",
        description="Current available balance in dollars, or None if error occurred",
    )
    error: str | None = Field(
        default=None,
        description="Error message if balance retrieval failed",
    )


class Account(BaseModel):
    """A financial account in Sequence."""

    id: str = Field(description="Unique identifier for the account")
    name: str = Field(description="Display name of the account")
    balance: AccountBalance = Field(description="Balance information")
    type: Literal["Pod", "Income Source", "Account"] = Field(
        description="Type of account"
    )


class AccountsResponseData(BaseModel):
    """Data payload for accounts response."""

    accounts: list[Account] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class AccountsResponse(BaseModel):
    """Response from the accounts endpoint."""

    message: str
    request_id: str = Field(alias="requestId")
    data: AccountsResponseData


class TriggerRuleResponseData(BaseModel):
    """Data payload for trigger rule response."""

    request_id: str = Field(alias="requestId")


class TriggerRuleResponse(BaseModel):
    """Response from triggering a rule."""

    code: str
    message: str
    data: TriggerRuleResponseData


class SequenceErrorResponse(BaseModel):
    """Error response from the API."""

    code: str
    message: str


class SequenceError(Exception):
    """Exception raised for Sequence API errors."""

    def __init__(self, code: str, message: str, status_code: int | None = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(f"{code}: {message}")
