from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from klik_trader.utils.models import IndicatorSnapshot


@dataclass
class IndicatorEngine:
    def compute(self, frame: pd.DataFrame) -> IndicatorSnapshot:
        values: Dict[str, float] = {}
        patterns: List[str] = []

        close = frame["close"]
        high = frame["high"]
        low = frame["low"]
        volume = frame["volume"]

        values["sma_20"] = close.rolling(20).mean().iloc[-1]
        values["sma_50"] = close.rolling(50).mean().iloc[-1]
        values["ema_20"] = close.ewm(span=20, adjust=False).mean().iloc[-1]
        values["ema_50"] = close.ewm(span=50, adjust=False).mean().iloc[-1]
        values["rsi_14"] = self._rsi(close, 14)
        values["atr_14"] = self._atr(frame, 14)
        values["adx_14"] = self._adx(frame, 14)
        values["cci_20"] = self._cci(frame, 20)
        values["stoch_k"] = self._stoch(frame, 14)[0]
        values["stoch_d"] = self._stoch(frame, 14)[1]
        values["macd"] = self._macd(close)[0]
        values["macd_signal"] = self._macd(close)[1]
        values["macd_hist"] = self._macd(close)[2]
        values["bb_upper"], values["bb_mid"], values["bb_lower"] = self._bollinger(close, 20)
        values["vwap"] = self._vwap(frame)
        values["obv"] = self._obv(close, volume)
        values["mfi"] = self._mfi(frame, 14)
        values["roc"] = self._roc(close, 12)
        values["momentum"] = close.diff(10).iloc[-1]
        values["williams_r"] = self._williams_r(frame, 14)
        values["ichimoku_base"], values["ichimoku_conv"] = self._ichimoku(frame)
        values["supertrend"] = self._supertrend(frame, 10, 3.0)
        values["pivot"] = self._pivot_point(frame)
        fibs = self._fibonacci_levels(frame)
        values.update(fibs)
        values["keltner_upper"], values["keltner_mid"], values["keltner_lower"] = self._keltner(frame)
        values["donchian_high"], values["donchian_low"] = self._donchian(frame, 20)
        values["trix"] = self._trix(close)
        values["tsi"] = self._tsi(close)
        values["ulcer_index"] = self._ulcer_index(close)
        values["volume_profile"] = self._volume_profile(close, volume)
        values["delta"] = (close.diff() * volume).iloc[-1]
        values["liquidity_score"] = self._liquidity_score(frame)

        patterns.extend(self._candlestick_patterns(frame))

        values = {key: float(value) if pd.notna(value) else 0.0 for key, value in values.items()}
        return IndicatorSnapshot(values=values, patterns=patterns)

    def _rsi(self, close: pd.Series, period: int) -> float:
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0).rolling(period).mean()
        loss = -delta.where(delta < 0, 0.0).rolling(period).mean()
        rs = gain / loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs)).iloc[-1]

    def _atr(self, frame: pd.DataFrame, period: int) -> float:
        high = frame["high"]
        low = frame["low"]
        close = frame["close"]
        prev_close = close.shift(1)
        tr = pd.concat(
            [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
            axis=1,
        ).max(axis=1)
        return tr.rolling(period).mean().iloc[-1]

    def _adx(self, frame: pd.DataFrame, period: int) -> float:
        high = frame["high"]
        low = frame["low"]
        close = frame["close"]
        plus_dm = high.diff().where((high.diff() > low.diff()) & (high.diff() > 0), 0.0)
        minus_dm = low.diff().where((low.diff() > high.diff()) & (low.diff() > 0), 0.0)
        tr = pd.concat(
            [(high - low), (high - close.shift()).abs(), (low - close.shift()).abs()],
            axis=1,
        ).max(axis=1)
        atr = tr.rolling(period).mean()
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
        return dx.rolling(period).mean().iloc[-1]

    def _cci(self, frame: pd.DataFrame, period: int) -> float:
        tp = (frame["high"] + frame["low"] + frame["close"]) / 3
        sma = tp.rolling(period).mean()
        mad = (tp - sma).abs().rolling(period).mean()
        return ((tp - sma) / (0.015 * mad)).iloc[-1]

    def _stoch(self, frame: pd.DataFrame, period: int) -> Tuple[float, float]:
        low_min = frame["low"].rolling(period).min()
        high_max = frame["high"].rolling(period).max()
        k = 100 * ((frame["close"] - low_min) / (high_max - low_min))
        d = k.rolling(3).mean()
        return k.iloc[-1], d.iloc[-1]

    def _macd(self, close: pd.Series) -> Tuple[float, float, float]:
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal = macd_line.ewm(span=9, adjust=False).mean()
        hist = macd_line - signal
        return macd_line.iloc[-1], signal.iloc[-1], hist.iloc[-1]

    def _bollinger(self, close: pd.Series, period: int) -> Tuple[float, float, float]:
        mid = close.rolling(period).mean()
        std = close.rolling(period).std()
        upper = mid + 2 * std
        lower = mid - 2 * std
        return upper.iloc[-1], mid.iloc[-1], lower.iloc[-1]

    def _vwap(self, frame: pd.DataFrame) -> float:
        pv = (frame["close"] * frame["volume"]).cumsum()
        vol = frame["volume"].cumsum()
        return (pv / vol).iloc[-1]

    def _obv(self, close: pd.Series, volume: pd.Series) -> float:
        direction = np.sign(close.diff()).fillna(0)
        return (direction * volume).cumsum().iloc[-1]

    def _mfi(self, frame: pd.DataFrame, period: int) -> float:
        tp = (frame["high"] + frame["low"] + frame["close"]) / 3
        money_flow = tp * frame["volume"]
        pos_flow = money_flow.where(tp.diff() > 0, 0.0).rolling(period).sum()
        neg_flow = money_flow.where(tp.diff() < 0, 0.0).rolling(period).sum()
        mfi = 100 - (100 / (1 + (pos_flow / neg_flow.replace(0, np.nan))))
        return mfi.iloc[-1]

    def _roc(self, close: pd.Series, period: int) -> float:
        return (close.diff(period) / close.shift(period)).iloc[-1] * 100

    def _williams_r(self, frame: pd.DataFrame, period: int) -> float:
        high_max = frame["high"].rolling(period).max()
        low_min = frame["low"].rolling(period).min()
        return -100 * (high_max - frame["close"]) / (high_max - low_min)

    def _ichimoku(self, frame: pd.DataFrame) -> Tuple[float, float]:
        nine_high = frame["high"].rolling(9).max()
        nine_low = frame["low"].rolling(9).min()
        conversion = (nine_high + nine_low) / 2
        period26_high = frame["high"].rolling(26).max()
        period26_low = frame["low"].rolling(26).min()
        base = (period26_high + period26_low) / 2
        return base.iloc[-1], conversion.iloc[-1]

    def _supertrend(self, frame: pd.DataFrame, period: int, multiplier: float) -> float:
        atr = self._atr(frame, period)
        hl2 = (frame["high"] + frame["low"]) / 2
        return (hl2 + multiplier * atr).iloc[-1]

    def _pivot_point(self, frame: pd.DataFrame) -> float:
        high = frame["high"].iloc[-2]
        low = frame["low"].iloc[-2]
        close = frame["close"].iloc[-2]
        return (high + low + close) / 3

    def _fibonacci_levels(self, frame: pd.DataFrame) -> Dict[str, float]:
        high = frame["high"].iloc[-50:].max()
        low = frame["low"].iloc[-50:].min()
        diff = high - low
        return {
            "fib_236": high - diff * 0.236,
            "fib_382": high - diff * 0.382,
            "fib_618": high - diff * 0.618,
        }

    def _keltner(self, frame: pd.DataFrame) -> Tuple[float, float, float]:
        ema = frame["close"].ewm(span=20, adjust=False).mean()
        atr = self._atr(frame, 20)
        upper = ema + atr * 2
        lower = ema - atr * 2
        return upper.iloc[-1], ema.iloc[-1], lower.iloc[-1]

    def _donchian(self, frame: pd.DataFrame, period: int) -> Tuple[float, float]:
        return frame["high"].rolling(period).max().iloc[-1], frame["low"].rolling(period).min().iloc[-1]

    def _trix(self, close: pd.Series) -> float:
        ema1 = close.ewm(span=15, adjust=False).mean()
        ema2 = ema1.ewm(span=15, adjust=False).mean()
        ema3 = ema2.ewm(span=15, adjust=False).mean()
        return ema3.pct_change().iloc[-1] * 100

    def _tsi(self, close: pd.Series) -> float:
        diff = close.diff()
        ema1 = diff.ewm(span=25, adjust=False).mean()
        ema2 = ema1.ewm(span=13, adjust=False).mean()
        abs_diff = diff.abs().ewm(span=25, adjust=False).mean().ewm(span=13, adjust=False).mean()
        return 100 * (ema2 / abs_diff).iloc[-1]

    def _ulcer_index(self, close: pd.Series) -> float:
        rolling_max = close.rolling(14).max()
        drawdown = ((close - rolling_max) / rolling_max) * 100
        return np.sqrt((drawdown.pow(2)).mean())

    def _volume_profile(self, close: pd.Series, volume: pd.Series) -> float:
        bins = pd.qcut(close, 10, duplicates="drop")
        profile = volume.groupby(bins).sum()
        return profile.max() if not profile.empty else 0.0

    def _liquidity_score(self, frame: pd.DataFrame) -> float:
        spread = frame["high"] - frame["low"]
        avg_spread = spread.rolling(20).mean().iloc[-1]
        return float((frame["volume"].iloc[-1] / avg_spread) if avg_spread else 0.0)

    def _candlestick_patterns(self, frame: pd.DataFrame) -> List[str]:
        patterns = []
        last = frame.iloc[-1]
        prev = frame.iloc[-2]
        body = abs(last["close"] - last["open"])
        total = last["high"] - last["low"]
        if total > 0 and body / total < 0.1:
            patterns.append("Doji")
        if last["close"] > last["open"] and (last["open"] - last["low"]) > body * 2:
            patterns.append("Hammer")
        if last["open"] > last["close"] and (last["high"] - last["open"]) > body * 2:
            patterns.append("Shooting Star")
        if last["close"] > last["open"] and prev["close"] < prev["open"] and last["close"] > prev["open"]:
            patterns.append("Bullish Engulfing")
        if last["close"] < last["open"] and prev["close"] > prev["open"] and last["close"] < prev["open"]:
            patterns.append("Bearish Engulfing")
        return patterns
