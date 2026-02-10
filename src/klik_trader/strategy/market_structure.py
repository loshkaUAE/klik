from __future__ import annotations

import pandas as pd


def market_structure(frame: pd.DataFrame) -> dict:
    highs = frame["high"].rolling(5).max()
    lows = frame["low"].rolling(5).min()
    last_high = highs.iloc[-1]
    prev_high = highs.iloc[-6]
    last_low = lows.iloc[-1]
    prev_low = lows.iloc[-6]

    higher_high = last_high > prev_high
    higher_low = last_low > prev_low
    lower_high = last_high < prev_high
    lower_low = last_low < prev_low

    if higher_high and higher_low:
        trend = "bullish"
    elif lower_high and lower_low:
        trend = "bearish"
    else:
        trend = "neutral"

    return {
        "trend": trend,
        "bos": "bullish" if higher_high else "bearish" if lower_low else "none",
        "choch": "bullish" if lower_high and higher_low else "bearish" if higher_high and lower_low else "none",
    }
