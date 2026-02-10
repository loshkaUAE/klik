from __future__ import annotations

import argparse

import pandas as pd

from klik_trader.indicators.engine import IndicatorEngine
from klik_trader.strategy.signal_engine import build_signal


def run_backtest(csv_path: str, symbol: str) -> None:
    frame = pd.read_csv(csv_path)
    engine = IndicatorEngine()
    signals = []
    for idx in range(100, len(frame)):
        window = frame.iloc[: idx + 1]
        engine.compute(window)
        signal = build_signal(symbol, window)
        if signal:
            signals.append(signal)
    print(f"Signals generated: {len(signals)}")
    if signals:
        last = signals[-1]
        print(f"Last signal: {last.symbol} {last.direction} {last.confidence:.1f}%")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--symbol", required=True)
    args = parser.parse_args()
    run_backtest(args.csv, args.symbol)


if __name__ == "__main__":
    main()
