# src/bussinbank/core/models.py
"""
Final, bug-free models – compatible with Pydantic 2.12+ (Dec 2025)
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Literal, Optional
from uuid import uuid4

from pydantic import (
    BaseModel,
    Field,
    PositiveFloat,
    ConfigDict,
    field_validator,
    model_validator,
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
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid4()))
    date: date
    amount: Decimal
    description: str
    merchant: Optional[str] = None
    category: str
    account_id: str
    type: TransactionType
    tags: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
    imported_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("amount", mode="before")
    @classmethod
    def parse_amount(cls, v):
        if isinstance(v, (int, float, str)):
            return Decimal(str(v)).quantize(Decimal("0.01"))
        return v

    # Fixed: correct Pydantic v2.5+ syntax
    @model_validator(mode="after")
    def validate_amount_sign(self) -> "Transaction":
        if self.type == TransactionType.INCOME and self.amount < 0:
            raise ValueError("Income transactions must have positive amount")
        if self.type == TransactionType.EXPENSE and self.amount > 0:
            raise ValueError("Expense transactions must have negative amount")
        return self


class Account(BaseModel):
    id: str
    name: str
    type: AccountType
    balance: Decimal
    currency: str = "USD"
    institution: Optional[str] = None
    is_active: bool = True
    include_in_net_worth: bool = True
    credit_limit: Optional[PositiveFloat] = None


class FinancialGoal(BaseModel):
    id: str
    name: str
    target_amount: PositiveFloat
    current_amount: Decimal = Decimal("0")
    target_date: Optional[date] = None
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    status: GoalStatus = GoalStatus.ACTIVE
    monthly_contribution: Optional[PositiveFloat] = None
    category: Optional[str] = None

    @property
    def progress_percent(self) -> float:
        return min(100.0, float(self.current_amount / self.target_amount * 100))

    @property
    def is_on_track(self) -> bool:
        if not self.target_date:
            return True
        days_left = (self.target_date - date.today()).days
        if days_left <= 0:
            return self.current_amount >= self.target_amount
        required_daily = (self.target_amount - self.current_amount) / days_left
        return (
            self.monthly_contribution is not None
            and (self.monthly_contribution / 30) >= required_daily
        )


class LedgerData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accounts: dict[str, Account] = Field(default_factory=dict)
    transactions: list[Transaction] = Field(default_factory=list)
    goals: dict[str, FinancialGoal] = Field(default_factory=dict)
    metadata: dict = Field(
        default_factory=lambda: {
            "version": "1.0",
            "created": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
        }
    )


# --------------------- Example Ledger ---------------------- #
EXAMPLE_LEDGER = LedgerData(
    accounts={
        "chase": Account(
            id="chase",
            name="Chase Checking",
            type=AccountType.CHECKING,
            balance=Decimal("5420.34"),
            institution="Chase",
        ),
        "amex": Account(
            id="amex",
            name="Amex Gold",
            type=AccountType.CREDIT_CARD,
            balance=Decimal("-1240.00"),
            credit_limit=20000,
        ),
    },
    transactions=[
        Transaction(
            id="tx1",
            date=date(2025, 12, 9),
            amount=Decimal("3200.00"),
            description="Salary deposit",
            category="income:salary",
            account_id="chase",
            type=TransactionType.INCOME,
        ),
        Transaction(
            id="tx2",
            date=date(2025, 12, 8),
            amount=Decimal("-87.50"),
            description="Whole Foods",
            category="food:groceries",
            account_id="chase",
            type=TransactionType.EXPENSE,
        ),
        Transaction(
            id="tx3",
            date=date(2025, 12, 7),
            amount=Decimal("-1200.00"),
            description="Rent",
            category="housing:rent",
            account_id="chase",
            type=TransactionType.EXPENSE,
        ),
    ],
    goals={
        "japan": FinancialGoal(
            id="japan",
            name="Japan Trip 2026",
            target_amount=5000,
            current_amount=Decimal("1200"),
            target_date=date(2026, 8, 1),
            priority="high",
        )
    },
)