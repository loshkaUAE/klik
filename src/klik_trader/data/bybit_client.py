from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Dict, List

import httpx

from klik_trader.utils.models import Candle


@dataclass
class BybitClient:
    api_key: str
    api_secret: str
    testnet: bool = True

    @property
    def base_url(self) -> str:
        return "https://api-testnet.bybit.com" if self.testnet else "https://api.bybit.com"

    def _sign(self, params: Dict[str, str]) -> str:
        payload = "&".join(f"{key}={value}" for key, value in sorted(params.items()))
        return hmac.new(self.api_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

    def _headers(self) -> Dict[str, str]:
        return {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-TIMESTAMP": str(int(time.time() * 1000)),
            "X-BAPI-RECV-WINDOW": "5000",
        }

    def fetch_klines(self, symbol: str, interval: str, limit: int = 200) -> List[Candle]:
        url = f"{self.base_url}/v5/market/kline"
        params = {
            "category": "linear",
            "symbol": symbol,
            "interval": interval,
            "limit": str(limit),
        }
        response = httpx.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        if data.get("retCode") != 0:
            raise RuntimeError(f"Bybit error: {data.get('retMsg')}")
        candles: List[Candle] = []
        for row in data["result"]["list"]:
            timestamp_ms, open_, high, low, close, volume, turnover = row
            candles.append(
                Candle(
                    timestamp=int(timestamp_ms),
                    open=float(open_),
                    high=float(high),
                    low=float(low),
                    close=float(close),
                    volume=float(volume),
                )
            )
        candles.sort(key=lambda candle: candle.timestamp)
        return candles
