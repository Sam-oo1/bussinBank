# src/bussinbank/core/models.py
"""
Core data models for BussinBank – the AI personal finance manager.

These Pydantic models are the single source of truth for:
- Every currency that moves
- Every account you own
- Every financial goal you're chasing

They power:
- Validation (no more "amount = -500 typos)
- JSON storage (data/ folder)
- Forecasting math
- Agent reasoning
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Literal, Optional

from pydantic import (
    BaseModel,
    Field,
    PositiveFloat,
    PositiveInt,
    ConfigDict,
    field_validator,
)

class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"


class AccountType(str, Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    INVESTMENT = "investment"
    CRYPTO = "crypto"
    LOAN = "loan"
    OTHER = "other"


class GoalStatus(str, Enum):
    ACTIVE = "active"
    ON_TRACK = "on_track"
    BEHIND = "behind"
    COMPLETED = "completed"
    PAUSED = "paused"

class Transaction(BaseModel):
    """A single money movement – the atomic unit of your financial life."""
    model_config = ConfigDict(frozen=True)  

    id: str = Field(..., description="UUID or hash – unique forever")
    date: date = Field(..., description="When the transaction happened")
    amount: Decimal = Field(..., description="Positive = money in, negative = money out")
    description: str = Field(..., description="Raw description from bank")
    merchant: Optional[str] = Field(default=None, description="Cleaned merchant name")
    category: str = Field(..., description="e.g. groceries, salary, rent")
    account_id: str = Field(..., description="Which account this hit")
    type: TransactionType = Field(..., description="income/expense/etc.")
    tags: list[str] = Field(default_factory=list, description="coffee, vacation, etc.")
    notes: Optional[str] = Field(default=None)

    @field_validator("amount", mode="before")
    @classmethod
    def parse_decimal(cls, v):
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v
    
class Account(BaseModel):
    """A bank account, credit card, crypto wallet, etc."""
    id: str = Field(..., description="Unique ID")
    name: str = Field(..., description="e.g. Chase Checking, Robinhood")
    type: AccountType
    balance: Decimal = Field(..., description="Current balance")
    currency: str = Field(default="USD")
    institution: Optional[str] = Field(default=None, description="Chase, Fidelity, etc.")
    is_active: bool = Field(default=True)
    include_in_net_worth: bool = Field(default=True)


class FinancialGoal(BaseModel):
    """A goal you're saving or paying down for."""
    id: str
    name: str = Field(..., description="e.g. Emergency Fund, Japan Trip 2026")
    target_amount: PositiveFloat
    current_amount: Decimal = Field(default=Decimal("0"))
    target_date: Optional[date] = None
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    status: GoalStatus = GoalStatus.ACTIVE
    monthly_contribution: Optional[PositiveFloat] = None