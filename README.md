# Klik Institutional Crypto Trading Dashboard

## 1) Architecture Diagram (Modules + Flow)

```
┌──────────────────────────┐
│     Bybit API Client      │  (REST: candles, tick data)
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│      Data Normalizer      │  (pandas DataFrame)
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│  Indicator Engine (30+)   │  (ATR, RSI, MACD, BB, VWAP, etc.)
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ Multi-Layer Signal Engine │  (Trend + Vol + Momentum + Structure + Liquidity + Time)
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│   Risk + Trade Advisor    │  (SL/TP1/TP2/TP3 + Quality Score)
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐          ┌──────────────────────────┐
│     FastAPI Dashboard     │◀────────▶│        WebSocket         │
└────────────┬─────────────┘          └──────────────────────────┘
             │
             ▼
┌──────────────────────────┐
│   Telegram Alert Module   │  (signals, TP/SL hits, errors)
└──────────────────────────┘
```

## 2) Features
- **Real-time dashboard** with candlestick chart, timeframe selection, indicator snapshot, candle patterns, and signal feed.
- **30+ technical indicators** (ATR, BB, SMA/EMA, VWAP, RSI, MACD, Stochastic, ADX, OBV, CCI, Ichimoku, SuperTrend, Pivot Points, Fibonacci, etc.).
- **Multi-layer signal engine** that requires alignment across trend, structure, volatility, momentum, liquidity, and time filters (90%+ confidence).
- **Manual trade advisor** with SL/TP levels and quality score.
- **Telegram alerts** for signals and system errors.
- **Backtest/Paper mode** switches via `ENVIRONMENT`.

## 3) Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env
```

Fill in:
- `BYBIT_API_KEY` and `BYBIT_API_SECRET`
- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`

## 4) Run

### Dashboard (includes live engine)
```bash
python -m klik_trader.cli dashboard
```

Open: `http://<server-ip>:8000`

### Engine only (no UI)
```bash
python -m klik_trader.cli engine
```

## 5) VPS Deployment
1. Provision Ubuntu 22.04+ VPS.
2. Install Python 3.11 and Git:
   ```bash
   sudo apt update
   sudo apt install -y python3.11 python3.11-venv git
   ```
3. Deploy:
   ```bash
   git clone <your-repo>
   cd klik
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install -e .
   cp .env.example .env
   ```
4. Start dashboard:
   ```bash
   python -m klik_trader.cli dashboard
   ```

## 6) Signal Format
Each signal includes:
```
SYMBOL
DIRECTION
ENTRY
STOP LOSS
TP1 / TP2 / TP3
RISK:REWARD
CONFIDENCE
WHY THIS TRADE WORKS
```

## 7) Professional Guardrails
- Deterministic calculations (no repainting).
- Confidence only when all filters align.
- SL and TP anchored to liquidity + volatility + structure.
- Capital preservation prioritized over frequency.
