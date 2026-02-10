from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Candle:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class IndicatorSnapshot:
    values: Dict[str, float]
    patterns: List[str]


@dataclass(frozen=True)
class Signal:
    symbol: str
    direction: str
    entry: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    risk_reward: float
    confidence: float
    explanation: str
    timestamp: int


@dataclass(frozen=True)
class TradePlan:
    symbol: str
    direction: str
    entry: float
    stop_loss: float
    take_profits: List[float]
    risk_reward: float
    quality_score: float
    explanation: str
