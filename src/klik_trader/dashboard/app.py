from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from typing import Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import pandas as pd

from klik_trader.advisor.manual_advisor import ManualTradeAdvisor
from klik_trader.utils.state import DashboardState

app = FastAPI(title="Klik Institutional Dashboard")
state = DashboardState()


class ConfigUpdate(BaseModel):
    symbol: str
    timeframe: str


class AdvisorRequest(BaseModel):
    symbol: str
    direction: str
    entry: float


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Klik Institutional Crypto Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-2.30.0.min.js"></script>
  <style>
    body { font-family: "Inter", Arial, sans-serif; background: #0c0f14; color: #e6e6e6; margin: 0; }
    header { padding: 20px; border-bottom: 1px solid #1c2230; display: flex; justify-content: space-between; align-items: center; }
    .container { padding: 20px; display: grid; gap: 20px; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }
    .card { background: #141925; border-radius: 12px; padding: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.25); }
    .controls { display: flex; gap: 12px; flex-wrap: wrap; }
    select, input, button { background: #1c2230; color: #e6e6e6; border: 1px solid #2a3144; padding: 8px 10px; border-radius: 8px; }
    button { cursor: pointer; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 8px; border-bottom: 1px solid #2a3144; text-align: left; }
    .pill { padding: 2px 8px; border-radius: 999px; background: #222a3a; display: inline-block; font-size: 12px; }
  </style>
</head>
<body>
<header>
  <div>
    <h1>Klik Institutional Crypto Dashboard</h1>
    <p>Real-time Bybit data, 30+ indicators, signal engine, and trade advisor.</p>
  </div>
  <div class="controls">
    <select id="symbol">
      <option>BTCUSDT</option>
      <option>ETHUSDT</option>
      <option>SOLUSDT</option>
    </select>
    <select id="timeframe">
      <option value="1">1m</option>
      <option value="5">5m</option>
      <option value="15" selected>15m</option>
      <option value="60">1h</option>
      <option value="240">4h</option>
      <option value="1440">1d</option>
    </select>
    <label><input type="checkbox" id="show-sma" checked /> SMA20</label>
    <label><input type="checkbox" id="show-ema" checked /> EMA20</label>
    <label><input type="checkbox" id="show-bb" /> Bollinger</label>
    <button onclick="updateConfig()">Update</button>
  </div>
</header>

<div class="container">
  <div class="card" style="grid-column: span 2;">
    <div id="chart"></div>
  </div>
  <div class="card">
    <h3>Indicators Snapshot</h3>
    <div id="indicators"></div>
  </div>
  <div class="card">
    <h3>Candlestick Patterns</h3>
    <div id="patterns"></div>
  </div>
  <div class="card">
    <h3>Signal Feed</h3>
    <table>
      <thead><tr><th>Time</th><th>Symbol</th><th>Dir</th><th>Conf</th></tr></thead>
      <tbody id="signals"></tbody>
    </table>
  </div>
  <div class="card">
    <h3>Manual Trade Advisor</h3>
    <input id="advisor-symbol" placeholder="Symbol" value="BTCUSDT" />
    <input id="advisor-direction" placeholder="LONG/SHORT" value="LONG" />
    <input id="advisor-entry" placeholder="Entry" value="0" />
    <button onclick="runAdvisor()">Calculate</button>
    <pre id="advisor-output"></pre>
  </div>
</div>

<script>
function updateConfig() {
  fetch('/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbol: document.getElementById('symbol').value, timeframe: document.getElementById('timeframe').value })
  });
}

function runAdvisor() {
  fetch('/api/advisor', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      symbol: document.getElementById('advisor-symbol').value,
      direction: document.getElementById('advisor-direction').value,
      entry: parseFloat(document.getElementById('advisor-entry').value)
    })
  }).then(res => res.json()).then(data => {
    document.getElementById('advisor-output').textContent = JSON.stringify(data, null, 2);
  });
}

const ws = new WebSocket(`ws://${window.location.host}/ws`);
ws.onmessage = (event) => {
  const payload = JSON.parse(event.data);
  renderChart(payload.candles);
  renderIndicators(payload.indicators);
  renderPatterns(payload.patterns);
  renderSignals(payload.signals);
};

function renderChart(candles) {
  const sma = rolling(candles.map(c => c.close), 20);
  const ema = emaSeries(candles.map(c => c.close), 20);
  const { upper, lower } = bollinger(candles.map(c => c.close), 20);
  const trace = {
    x: candles.map(c => new Date(c.timestamp)),
    open: candles.map(c => c.open),
    high: candles.map(c => c.high),
    low: candles.map(c => c.low),
    close: candles.map(c => c.close),
    type: 'candlestick',
  };
  const traces = [trace];
  if (document.getElementById('show-sma').checked) {
    traces.push({ x: trace.x, y: sma, type: 'scatter', name: 'SMA20', line: { color: '#5cc8ff' } });
  }
  if (document.getElementById('show-ema').checked) {
    traces.push({ x: trace.x, y: ema, type: 'scatter', name: 'EMA20', line: { color: '#f5a623' } });
  }
  if (document.getElementById('show-bb').checked) {
    traces.push({ x: trace.x, y: upper, type: 'scatter', name: 'BB Upper', line: { color: '#7f8cff', dash: 'dot' } });
    traces.push({ x: trace.x, y: lower, type: 'scatter', name: 'BB Lower', line: { color: '#7f8cff', dash: 'dot' } });
  }
  Plotly.newPlot('chart', traces, { margin: { t: 20 }, paper_bgcolor: '#141925', plot_bgcolor: '#141925' });
}

function renderIndicators(indicators) {
  const entries = Object.entries(indicators).slice(0, 20);
  document.getElementById('indicators').innerHTML = entries.map(([key, value]) => {
    return `<div><span class="pill">${key}</span> ${value.toFixed(2)}</div>`;
  }).join('');
}

function rolling(values, period) {
  return values.map((_, idx) => {
    if (idx + 1 < period) return null;
    const slice = values.slice(idx + 1 - period, idx + 1);
    return slice.reduce((a, b) => a + b, 0) / period;
  });
}

function emaSeries(values, period) {
  const k = 2 / (period + 1);
  const result = [];
  let ema = values[0] || 0;
  values.forEach((value, idx) => {
    if (idx === 0) {
      ema = value;
    } else {
      ema = (value - ema) * k + ema;
    }
    result.push(ema);
  });
  return result;
}

function bollinger(values, period) {
  const upper = [];
  const lower = [];
  values.forEach((_, idx) => {
    if (idx + 1 < period) {
      upper.push(null);
      lower.push(null);
      return;
    }
    const slice = values.slice(idx + 1 - period, idx + 1);
    const mean = slice.reduce((a, b) => a + b, 0) / period;
    const variance = slice.reduce((a, b) => a + (b - mean) ** 2, 0) / period;
    const std = Math.sqrt(variance);
    upper.push(mean + 2 * std);
    lower.push(mean - 2 * std);
  });
  return { upper, lower };
}

function renderPatterns(patterns) {
  document.getElementById('patterns').innerHTML = patterns.length
    ? patterns.map(p => `<div class="pill">${p}</div>`).join(' ')
    : '<em>No patterns detected</em>';
}

function renderSignals(signals) {
  document.getElementById('signals').innerHTML = signals.slice(0, 8).map(sig => {
    return `<tr><td>${new Date(sig.timestamp * 1000).toLocaleTimeString()}</td><td>${sig.symbol}</td><td>${sig.direction}</td><td>${sig.confidence.toFixed(1)}%</td></tr>`;
  }).join('');
}
</script>
</body>
</html>
"""


@app.get("/")
async def dashboard() -> HTMLResponse:
    return HTMLResponse(HTML_TEMPLATE)


@app.post("/api/config")
async def update_config(update: ConfigUpdate) -> Dict[str, str]:
    state.selected_symbol = update.symbol
    state.selected_timeframe = update.timeframe
    return {"symbol": update.symbol, "timeframe": update.timeframe}


@app.post("/api/advisor")
async def manual_advisor(request: AdvisorRequest) -> dict:
    if not state.candles:
        return {"error": "No candle data loaded yet."}
    frame = pd.DataFrame(state.candles)
    advisor = ManualTradeAdvisor()
    plan = advisor.build_plan(request.symbol, request.direction, request.entry, frame)
    return asdict(plan)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            await websocket.send_text(json.dumps(serialize_state()))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return


def serialize_state() -> dict:
    return {
        "candles": state.candles,
        "indicators": state.indicators,
        "patterns": state.patterns,
        "signals": [asdict(signal) for signal in list(state.signals)],
    }
