from __future__ import annotations

import argparse
import asyncio
import threading

import uvicorn

from klik_trader.config.settings import load_settings
from klik_trader.dashboard.app import app, state
from klik_trader.data.bybit_client import BybitClient
from klik_trader.engine import MarketEngine
from klik_trader.telegram.bot import TelegramNotifier


def build_engine() -> MarketEngine:
    settings = load_settings()
    notifier = None
    if settings.telegram.token and settings.telegram.chat_id:
        notifier = TelegramNotifier(settings.telegram.token, settings.telegram.chat_id)
    client = BybitClient(
        api_key=settings.bybit.api_key,
        api_secret=settings.bybit.api_secret,
        testnet=settings.bybit.testnet,
    )
    return MarketEngine(
        client=client,
        symbol=settings.symbol,
        timeframe=settings.timeframe,
        candle_limit=settings.candle_limit,
        notifier=notifier,
        dashboard_state=state,
        confidence_threshold=settings.confidence_threshold,
    )


async def run_engine() -> None:
    engine = build_engine()
    await engine.run(interval=10)


def run_dashboard() -> None:
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_until_complete, args=(run_engine(),), daemon=True)
    thread.start()
    uvicorn.run(app, host="0.0.0.0", port=8000)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Klik Institutional Dashboard")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("dashboard", help="Run dashboard with live Bybit data")
    sub.add_parser("engine", help="Run signal engine without UI")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "dashboard":
        run_dashboard()
    elif args.command == "engine":
        asyncio.run(run_engine())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
