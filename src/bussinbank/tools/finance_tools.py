# src/bussinbank/tools/finance_tools.py
"""These are the only functions the AI is allowed to call."""

from datetime import date as dt_date  # avoid conflict with date in tools
from decimal import Decimal
from typing import Literal
from langchain_core.tools import tool

from bussinbank.core.ledger import ledger
from bussinbank.core.forecaster import forecaster

@tool
def get_net_worth() -> str:
    """Return current net worth with explanation."""
    worth = ledger.net_worth
    return f"Your current net worth is ${worth:,.2f}"

@tool
def get_runway() -> str:
    """How many days of cash left?"""
    days = ledger.runway_days
    if days == "infinite":
        return "You have infinite runway — you're either rich or not spending anything."
    return f"You have {days} days of runway at current burn rate."

@tool
def get_monthly_burn() -> str:
    """Gives your monthly expenditure"""
    burn = ledger.monthly_burn_rate
    return f"You burn ${burn:,.2f} per month on average."

@tool
def get_spending_this_month() -> str:
    """Gives expenditure of current month."""
    spending = ledger.get_spending_this_month()
    return f"You've spent ${spending:,.2f} so far this month."

@tool
def project_future_balance(target_date: str, extra_savings: float = 0) -> str:
    """Predicts your cash balance on a future date (YYYY-MM-DD)."""
    from datetime import date
    from decimal import Decimal

    try:
        target = date.fromisoformat(target_date.strip())
    except:
        return "Please use a valid date format: YYYY-MM-DD"

    today = date.today()
    if target <= today:
        return f"{target_date} is today or in the past. Ask for a future date like 2026-12-31."

    projected = forecaster.project_balance(target, Decimal(str(extra_savings)))
    return f"On {target_date}, you'll have ≈ ${projected:,.2f} in liquid cash (+${extra_savings:,.0f}/mo saved)"


# List of tools the AI can see
TOOLS = [
    get_net_worth,
    get_runway,
    get_monthly_burn,
    get_spending_this_month,
    project_future_balance,
]