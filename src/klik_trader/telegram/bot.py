from __future__ import annotations

from dataclasses import dataclass

from telegram import Bot

from klik_trader.utils.models import Signal


@dataclass
class TelegramNotifier:
    token: str
    chat_id: str

    def __post_init__(self) -> None:
        self.bot = Bot(token=self.token)

    async def send_message(self, message: str) -> None:
        await self.bot.send_message(chat_id=self.chat_id, text=message)

    async def send_signal(self, signal: Signal) -> None:
        message = (
            "🚨 High-Probability Signal\n"
            f"Symbol: {signal.symbol}\n"
            f"Direction: {signal.direction}\n"
            f"Entry: {signal.entry:.2f}\n"
            f"Stop Loss: {signal.stop_loss:.2f}\n"
            f"TP1: {signal.take_profit_1:.2f}\n"
            f"TP2: {signal.take_profit_2:.2f}\n"
            f"TP3: {signal.take_profit_3:.2f}\n"
            f"R:R: {signal.risk_reward:.2f}\n"
            f"Confidence: {signal.confidence:.1f}%\n"
            f"Why: {signal.explanation}"
        )
        await self.send_message(message)

    async def send_error(self, error: str) -> None:
        await self.send_message(f"⚠️ System error: {error}")
