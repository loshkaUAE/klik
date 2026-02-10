from __future__ import annotations

import pandas as pd


def atr(frame: pd.DataFrame, period: int = 14) -> float:
    high = frame["high"]
    low = frame["low"]
    close = frame["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.rolling(period).mean().iloc[-1]


def volatility_regime(frame: pd.DataFrame) -> dict:
    current_atr = atr(frame)
    baseline = atr(frame.iloc[:-20]) if len(frame) > 40 else current_atr
    regime = "high" if current_atr > baseline * 1.2 else "low" if current_atr < baseline * 0.8 else "normal"
    return {"atr": float(current_atr), "regime": regime}
