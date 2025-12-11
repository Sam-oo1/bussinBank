# src/bussinbank/core/forecaster.py
"""
Future-predicting engine for BussinBank.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Tuple, Literal

from bussinbank.core.ledger import ledger  # ← Fixed: import the real ledger object

AVG_DAYS_PER_MONTH = Decimal("30.4375")


class Forecaster:
    """Predicts your financial future based on real behavior."""

    def __init__(self):
        self.ledger = ledger  # Uses the global singleton

    def project_balance(
        self,
        target_date: date,
        extra_monthly_savings: Decimal = Decimal("0"),
        one_time_expenses: List[Tuple[date, Decimal]] = None,
    ) -> Decimal:
        """
        What will your total liquid cash be on target_date?
        (checking + savings only)
        """
        if one_time_expenses is None:
            one_time_expenses = []

        days_ahead = (target_date - date.today()).days
        if days_ahead <= 0:
            return self._current_liquid_cash()

        # Average daily net flow (income - expenses)
        daily_net = self._average_daily_net_flow()

        # Adjust for extra savings
        daily_net += extra_monthly_savings / AVG_DAYS_PER_MONTH

        projected = self._current_liquid_cash() + (daily_net * days_ahead)

        # Subtract one-time expenses
        for exp_date, amount in one_time_expenses:
            if date.today() < exp_date <= target_date:
                projected -= amount

        return projected.quantize(Decimal("0.01"))

    def months_until_goal(self, target_amount: Decimal) -> int | Literal["never"]:
        """How many months until net worth hits target?"""
        current = self.ledger.net_worth
        if current >= target_amount:
            return 0

        monthly_net = self._average_monthly_net_flow()
        if monthly_net <= 0:
            return "never"

        months = (target_amount - current) / monthly_net
        return max(1, int(months.to_integral_value() + 1))  # ceiling

    def forecast_monthly_balances(
        self, months_ahead: int = 24
    ) -> List[Tuple[date, Decimal]]:
        """Returns list of (month_start_date, projected_liquid_balance)"""
        balances = []
        current_cash = self._current_liquid_cash()
        daily_net = self._average_daily_net_flow()

        for i in range(months_ahead + 1):
            month_date = date.today().replace(day=1) + timedelta(days=32 * i)
            month_date = month_date.replace(day=1)  # first of month
            days = (month_date - date.today()).days + i  # approx
            projected = current_cash + daily_net * days
            balances.append((month_date, projected.quantize(Decimal("0.01"))))

        return balances

    def when_can_i_retire(
        self,
        annual_spending: Decimal,
        safe_withdrawal_rate: Decimal = Decimal("0.04"),
    ) -> date | Literal["never"]:
        """Classic 4% rule — when can you retire?"""
        required_nest_egg = annual_spending / safe_withdrawal_rate
        months = self.months_until_goal(required_nest_egg)
        if months == "never":
            return "never"
        return date.today() + timedelta(days=30 * months)

    # ──────── Private helpers ────────
    def _current_liquid_cash(self) -> Decimal:
        return sum(
            acc.balance
            for acc in self.ledger.data.accounts.values()
            if acc.type in ("checking", "savings") and acc.balance > 0
        )

    def _average_daily_net_flow(self) -> Decimal:
        cutoff = date.today() - timedelta(days=90)  # 3 months of history
        total = Decimal("0")
        count = 0
        for tx in self.ledger.data.transactions:
            if tx.date >= cutoff:
                total += tx.amount
                count += 1
        return (total / max(1, count)) if count > 0 else Decimal("0")

    def _average_monthly_net_flow(self) -> Decimal:
        return self._average_daily_net_flow() * AVG_DAYS_PER_MONTH


# Global forecaster — used by the AI will use
forecaster = Forecaster()