from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Protocol

import pandas as pd

from klik_trader.utils.models import Candle


class MarketDataProvider(Protocol):
    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> List[Candle]:
        ...


@dataclass
class LocalCSVDataProvider:
    path: str

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> List[Candle]:
        frame = pd.read_csv(self.path)
        frame = frame.tail(limit)
        candles = []
        for _, row in frame.iterrows():
            candles.append(
                Candle(
                    timestamp=pd.to_datetime(row["timestamp"]).to_pydatetime(),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row.get("volume", 0.0)),
                )
            )
        return candles


@dataclass
class CCXTDataProvider:
    exchange_id: str

    def __post_init__(self) -> None:
        import ccxt

        exchange_class = getattr(ccxt, self.exchange_id)
        self.exchange = exchange_class({"enableRateLimit": True})

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> List[Candle]:
        raw = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        candles: List[Candle] = []
        for timestamp, open_, high, low, close, volume in raw:
            candles.append(
                Candle(
                    timestamp=datetime.utcfromtimestamp(timestamp / 1000),
                    open=float(open_),
                    high=float(high),
                    low=float(low),
                    close=float(close),
                    volume=float(volume),
                )
            )
        return candles
