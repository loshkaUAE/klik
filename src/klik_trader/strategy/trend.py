from __future__ import annotations

import pandas as pd


def trend_bias(frame: pd.DataFrame) -> dict:
    close = frame["close"]
    htf = close.ewm(span=50, adjust=False).mean().iloc[-1]
    ltf = close.ewm(span=20, adjust=False).mean().iloc[-1]
    current = close.iloc[-1]
    return {
        "htf": "bullish" if current > htf else "bearish" if current < htf else "neutral",
        "ltf": "bullish" if current > ltf else "bearish" if current < ltf else "neutral",
    }
