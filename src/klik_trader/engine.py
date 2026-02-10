from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional

import pandas as pd

from klik_trader.data.bybit_client import BybitClient
from klik_trader.indicators.engine import IndicatorEngine
from klik_trader.strategy.signal_engine import build_signal
from klik_trader.telegram.bot import TelegramNotifier
from klik_trader.utils.models import Signal
from klik_trader.utils.state import DashboardState


@dataclass
class MarketEngine:
    client: BybitClient
    symbol: str
    timeframe: str
    candle_limit: int
    notifier: Optional[TelegramNotifier] = None
    dashboard_state: Optional[DashboardState] = None
    confidence_threshold: float = 0.9

    async def run(self, interval: int = 10) -> None:
        while True:
            await self.refresh()
            await asyncio.sleep(interval)

    async def refresh(self) -> None:
        symbol = self.dashboard_state.selected_symbol or self.symbol if self.dashboard_state else self.symbol
        timeframe = self.dashboard_state.selected_timeframe or self.timeframe if self.dashboard_state else self.timeframe
        candles = self.client.fetch_klines(symbol, timeframe, self.candle_limit)
        frame = pd.DataFrame([candle.__dict__ for candle in candles])
        indicators = IndicatorEngine().compute(frame)
        signal = build_signal(symbol, frame)
        if signal and signal.confidence >= self.confidence_threshold * 100:
            await self._publish_signal(signal)
        if self.dashboard_state:
            self.dashboard_state.candles = frame.tail(200).to_dict(orient="records")
            self.dashboard_state.indicators = indicators.values
            self.dashboard_state.patterns = indicators.patterns

    async def _publish_signal(self, signal: Signal) -> None:
        if self.notifier:
            await self.notifier.send_signal(signal)
        if self.dashboard_state:
            self.dashboard_state.add_signal(signal)
