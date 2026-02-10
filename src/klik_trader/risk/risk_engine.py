from __future__ import annotations

from dataclasses import dataclass

from klik_trader.utils.models import TradePlan


@dataclass
class RiskEngine:
    account_balance: float
    max_risk_per_trade: float
    max_daily_drawdown: float

    def position_size(self, entry: float, stop_loss: float) -> float:
        risk_amount = self.account_balance * self.max_risk_per_trade
        per_unit_risk = abs(entry - stop_loss)
        if per_unit_risk == 0:
            return 0.0
        return risk_amount / per_unit_risk

    def evaluate_trade(self, plan: TradePlan) -> dict:
        position_size = self.position_size(plan.entry, plan.stop_loss)
        return {
            "position_size": position_size,
            "max_risk": self.account_balance * self.max_risk_per_trade,
            "daily_drawdown_limit": self.account_balance * self.max_daily_drawdown,
        }
