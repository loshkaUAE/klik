from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class BybitSettings:
    api_key: str
    api_secret: str
    testnet: bool


@dataclass(frozen=True)
class TelegramSettings:
    token: str
    chat_id: str


@dataclass(frozen=True)
class AppSettings:
    environment: str
    symbol: str
    timeframe: str
    candle_limit: int
    confidence_threshold: float
    bybit: BybitSettings
    telegram: TelegramSettings


def _env(name: str, default: str) -> str:
    value = os.getenv(name, default)
    return value.strip()


def load_settings() -> AppSettings:
    load_dotenv()
    bybit = BybitSettings(
        api_key=_env("BYBIT_API_KEY", ""),
        api_secret=_env("BYBIT_API_SECRET", ""),
        testnet=_env("BYBIT_TESTNET", "true").lower() in {"1", "true", "yes"},
    )
    telegram = TelegramSettings(
        token=_env("TELEGRAM_BOT_TOKEN", ""),
        chat_id=_env("TELEGRAM_CHAT_ID", ""),
    )
    return AppSettings(
        environment=_env("ENVIRONMENT", "paper"),
        symbol=_env("SYMBOL", "BTCUSDT"),
        timeframe=_env("TIMEFRAME", "15"),
        candle_limit=int(_env("CANDLE_LIMIT", "300")),
        confidence_threshold=float(_env("CONFIDENCE_THRESHOLD", "0.9")),
        bybit=bybit,
        telegram=telegram,
    )
