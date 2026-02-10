from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

import pandas as pd

from klik_trader.indicators.engine import IndicatorEngine
from klik_trader.strategy.liquidity import liquidity_zones
from klik_trader.strategy.market_structure import market_structure
from klik_trader.strategy.time_filter import in_kill_zone
from klik_trader.strategy.trend import trend_bias
from klik_trader.strategy.volatility import volatility_regime
from klik_trader.utils.models import Signal


@dataclass
class SignalDecision:
    aligned: bool
    confidence: float
    explanation: str
    direction: Optional[str]


def evaluate_signal(frame: pd.DataFrame, indicators: Dict[str, float]) -> SignalDecision:
    structure = market_structure(frame)
    liquidity = liquidity_zones(frame)
    trend = trend_bias(frame)
    volatility = volatility_regime(frame)

    confidence = 0.0
    notes = []

    direction = None
    if trend["htf"] == trend["ltf"] == "bullish":
        direction = "LONG"
        confidence += 0.2
        notes.append("HTF/LTF bullish alignment")
    elif trend["htf"] == trend["ltf"] == "bearish":
        direction = "SHORT"
        confidence += 0.2
        notes.append("HTF/LTF bearish alignment")
    else:
        notes.append("Trend misalignment")

    if structure["trend"] != "neutral":
        confidence += 0.2
        notes.append(f"Structure {structure['trend']} BOS {structure['bos']}")

    if volatility["regime"] != "low":
        confidence += 0.15
        notes.append(f"Volatility {volatility['regime']}")

    if in_kill_zone(datetime.utcnow()):
        confidence += 0.1
        notes.append("Kill zone active")

    if indicators["rsi_14"] > 55 and direction == "LONG":
        confidence += 0.1
        notes.append("RSI supports long")
    if indicators["rsi_14"] < 45 and direction == "SHORT":
        confidence += 0.1
        notes.append("RSI supports short")

    if indicators["macd"] > indicators["macd_signal"] and direction == "LONG":
        confidence += 0.1
        notes.append("MACD momentum up")
    if indicators["macd"] < indicators["macd_signal"] and direction == "SHORT":
        confidence += 0.1
        notes.append("MACD momentum down")

    if abs(liquidity["sweep_high"] - liquidity["sweep_low"]) > 0:
        confidence += 0.05
        notes.append("Liquidity zones mapped")

    confidence = min(confidence, 0.99)
    aligned = confidence >= 0.9 and direction is not None
    return SignalDecision(aligned=aligned, confidence=confidence, explanation="; ".join(notes), direction=direction)


def build_signal(symbol: str, frame: pd.DataFrame) -> Optional[Signal]:
    indicator_engine = IndicatorEngine()
    snapshot = indicator_engine.compute(frame)
    decision = evaluate_signal(frame, snapshot.values)
    if not decision.aligned or decision.direction is None:
        return None

    close = frame["close"].iloc[-1]
    atr = snapshot.values["atr_14"]
    liquidity = liquidity_zones(frame)

    if decision.direction == "LONG":
        stop_loss = liquidity["sweep_low"] - atr * 0.5
        tp1 = close + (close - stop_loss) * 2
        tp2 = close + (close - stop_loss) * 3
        tp3 = liquidity["sweep_high"] + atr * 1.5
    else:
        stop_loss = liquidity["sweep_high"] + atr * 0.5
        tp1 = close - (stop_loss - close) * 2
        tp2 = close - (stop_loss - close) * 3
        tp3 = liquidity["sweep_low"] - atr * 1.5

    risk_reward = abs((tp1 - close) / (close - stop_loss))

    return Signal(
        symbol=symbol,
        direction=decision.direction,
        entry=close,
        stop_loss=stop_loss,
        take_profit_1=tp1,
        take_profit_2=tp2,
        take_profit_3=tp3,
        risk_reward=risk_reward,
        confidence=decision.confidence * 100,
        explanation=decision.explanation,
        timestamp=int(datetime.utcnow().timestamp()),
    )
