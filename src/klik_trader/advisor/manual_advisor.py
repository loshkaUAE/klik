from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from klik_trader.indicators.engine import IndicatorEngine
from klik_trader.strategy.liquidity import liquidity_zones
from klik_trader.strategy.market_structure import market_structure
from klik_trader.strategy.trend import trend_bias
from klik_trader.strategy.volatility import volatility_regime
from klik_trader.utils.models import TradePlan


@dataclass
class ManualTradeAdvisor:
    def build_plan(self, symbol: str, direction: str, entry: float, frame: pd.DataFrame) -> TradePlan:
        indicators = IndicatorEngine().compute(frame)
        liquidity = liquidity_zones(frame)
        structure = market_structure(frame)
        trend = trend_bias(frame)
        volatility = volatility_regime(frame)

        atr = indicators.values["atr_14"]
        if direction == "LONG":
            stop_loss = liquidity["sweep_low"] - atr * 0.6
            tp1 = entry + (entry - stop_loss) * 2
            tp2 = entry + (entry - stop_loss) * 3
            tp3 = liquidity["sweep_high"] + atr * 1.5
        else:
            stop_loss = liquidity["sweep_high"] + atr * 0.6
            tp1 = entry - (stop_loss - entry) * 2
            tp2 = entry - (stop_loss - entry) * 3
            tp3 = liquidity["sweep_low"] - atr * 1.5

        risk_reward = abs((tp1 - entry) / (entry - stop_loss))
        quality = 50.0
        if trend["htf"] == trend["ltf"]:
            quality += 20
        if volatility["regime"] != "low":
            quality += 15
        if structure["trend"] != "neutral":
            quality += 10
        if risk_reward >= 2:
            quality += 5

        explanation = (
            f"Trend {trend['htf']}/{trend['ltf']}; Structure {structure['trend']} BOS {structure['bos']}; "
            f"Volatility {volatility['regime']} ATR {atr:.2f}; Liquidity sweep {liquidity['sweep_high']:.2f}/{liquidity['sweep_low']:.2f}"
        )

        return TradePlan(
            symbol=symbol,
            direction=direction,
            entry=entry,
            stop_loss=stop_loss,
            take_profits=[tp1, tp2, tp3],
            risk_reward=risk_reward,
            quality_score=min(quality, 100.0),
            explanation=explanation,
        )
