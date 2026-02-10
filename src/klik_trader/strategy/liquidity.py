from __future__ import annotations

import pandas as pd


def liquidity_zones(frame: pd.DataFrame) -> dict:
    highs = frame["high"].iloc[-50:]
    lows = frame["low"].iloc[-50:]
    equal_highs = highs[(highs.diff().abs() < highs.mean() * 0.001)].mean()
    equal_lows = lows[(lows.diff().abs() < lows.mean() * 0.001)].mean()
    sweep_high = highs.max()
    sweep_low = lows.min()
    return {
        "equal_highs": float(equal_highs) if pd.notna(equal_highs) else float(sweep_high),
        "equal_lows": float(equal_lows) if pd.notna(equal_lows) else float(sweep_low),
        "sweep_high": float(sweep_high),
        "sweep_low": float(sweep_low),
    }
