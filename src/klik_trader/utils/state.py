from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List

from klik_trader.utils.models import Signal


@dataclass
class DashboardState:
    candles: List[dict] = field(default_factory=list)
    indicators: Dict[str, float] = field(default_factory=dict)
    patterns: List[str] = field(default_factory=list)
    signals: Deque[Signal] = field(default_factory=lambda: deque(maxlen=200))
    winrate: float = 0.0
    drawdown: float = 0.0
    equity_curve: List[float] = field(default_factory=list)
    last_error: str = ""
    selected_symbol: str = ""
    selected_timeframe: str = ""

    def add_signal(self, signal: Signal) -> None:
        self.signals.appendleft(signal)
