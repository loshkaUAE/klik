from __future__ import annotations

from dataclasses import dataclass
from typing import List

from klik_trader.utils.models import Signal


@dataclass
class ExecutionResult:
    mode: str
    accepted: bool
    message: str


@dataclass
class ExecutionEngine:
    mode: str

    def route_signal(self, signal: Signal) -> ExecutionResult:
        if self.mode == "backtest":
            return ExecutionResult(mode=self.mode, accepted=True, message="Recorded for backtest")
        if self.mode == "paper":
            return ExecutionResult(mode=self.mode, accepted=True, message="Paper trade placed")
        if self.mode == "live":
            return ExecutionResult(mode=self.mode, accepted=False, message="Live execution not wired")
        return ExecutionResult(mode=self.mode, accepted=False, message="Unknown mode")

    def route_batch(self, signals: List[Signal]) -> List[ExecutionResult]:
        return [self.route_signal(signal) for signal in signals]
