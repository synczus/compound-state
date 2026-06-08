#!/usr/bin/env python3
"""
Synapse Compound Dashboard — FastAPI Server
Serves the main dashboard UI + REST API for trade signals, charts, and compound state.
"""
import json
import os
import sqlite3
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

KESTREL = Path(__file__).resolve().parent.parent

app = FastAPI(title="Synapse Compound Dashboard")

# ── API Routes ───────────────────────────────────────────────────────────────

@app.get("/api/signals")
async def get_signals(min_edge: float = 0, limit: int = 50):
    """Return enriched trade signals from the pipeline."""
    feed_path = KESTREL / "data" / "trade_signals.json"
    if not feed_path.exists():
        return {"signals": [], "error": "no data yet"}
    data = json.loads(feed_path.read_text())
    signals = [s for s in data.get("signals", []) if s.get("edge_score", 0) >= min_edge]
    return {
        "signals": signals[:limit],
        "total": len(data.get("signals", [])),
        "actionable": len([s for s in signals if s.get("rating") in ("HIGH", "TRADABLE")]),
        "generated_at": data.get("generated_at"),
        "live_prices": data.get("live_prices", {}),
        "atr_summary": data.get("atr_summary", {}),
    }

@app.get("/api/chart/{symbol}")
async def get_chart(symbol: str, days: int = Query(1, ge=1, le=7)):
    """Return OHLC data for candlestick chart rendering."""
    coin_map = {
        "BTC": "bitcoin", "BTC-USD": "bitcoin",
        "ETH": "ethereum", "ETH-USD": "ethereum",
        "SOL": "solana", "SOL-USD": "solana",
    }
    coin_id = coin_map.get(symbol)
    if not coin_id:
        return {"error": f"Unknown symbol: {symbol}"}
    
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc?vs_currency=usd&days={days}"
        req = urllib.request.Request(url, headers={"User-Agent": "Kestrel/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            ohlc = json.loads(r.read().decode())
        
        # Convert to standard format
        candles = []
        for c in ohlc:
            candles.append({
                "time": c[0] // 1000,  # ms → seconds
                "open": c[1],
                "high": c[2],
                "low": c[3],
                "close": c[4],
            })
        
        return {"symbol": symbol, "candles": candles, "count": len(candles)}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/prices")
async def get_prices():
    """Return current live prices for tracked assets."""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd"
        req = urllib.request.Request(url, headers={"User-Agent": "Kestrel/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/state")
async def get_state():
    """Return compound state summary."""
    state_path = KESTREL / "compound-state.json"
    if state_path.exists():
        return json.loads(state_path.read_text())
    return {"status": "no state file"}

@app.get("/api/striker-stats")
async def get_striker_stats():
    """Return Striker DB statistics."""
    db_path = KESTREL / "kestrel_signals.db"
    if not db_path.exists():
        return {"error": "no DB"}
    
    stats = {}
    try:
        conn = sqlite3.connect(str(db_path))
        stats["total_signals"] = conn.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
        stats["last_signal"] = conn.execute("SELECT MAX(timestamp) FROM signals").fetchone()[0]
        stats["by_symbol"] = {}
        for r in conn.execute("SELECT symbol, COUNT(*) as c FROM signals GROUP BY symbol ORDER BY c DESC").fetchall():
            stats["by_symbol"][r[0]] = r[1]
        stats["by_direction"] = {}
        for r in conn.execute("SELECT direction, COUNT(*) as c FROM signals GROUP BY direction").fetchall():
            stats["by_direction"][r[0]] = r[1]
        stats["high_confidence"] = conn.execute("SELECT COUNT(*) FROM signals WHERE confidence >= 0.5").fetchone()[0]
        conn.close()
    except Exception as e:
        stats["error"] = str(e)
    return stats


# ── Dashboard HTML ───────────────────────────────────────────────────────────

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Synapse Compound — Dashboard</title>
<script src="https://unpkg.com/lightweight-charts@4.0.1/dist/lightweight-charts.standalone.production.js"></script>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
:root {
  --bg: #0a0e17;
  --card: #111827;
  --border: #1e293b;
  --green: #22c55e;
  --red: #ef4444;
  --blue: #3b82f6;
  --purple: #a855f7;
  --text: #e2e8f0;
  --muted: #64748b;
  --accent: #06b6d4;
}
body {
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  padding: 16px;
}
.header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 20px; background: var(--card); border: 1px solid var(--border);
  border-radius: 12px; margin-bottom: 16px;
}
.header h1 { font-size: 20px; font-weight: 700; color: var(--accent); }
.header h1 span { color: var(--text); font-weight: 300; }
.header-right { display: flex; gap: 16px; align-items: center; font-size: 13px; }
.status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
.status-dot.green { background: var(--green); }
.status-dot.red { background: var(--red); }
.status-dot.yellow { background: #eab308; }
.price-ticker { display: flex; gap: 20px; }
.price-ticker .item { display: flex; align-items: center; gap: 6px; }
.price-ticker .sym { font-weight: 600; font-size: 13px; }
.price-ticker .val { font-weight: 700; font-size: 14px; }
.price-ticker .chg { font-size: 12px; }

.grid { display: grid; gap: 12px; }
.grid-2 { grid-template-columns: 1fr 1fr; }
.grid-3 { grid-template-columns: 2fr 1fr; }
.card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 12px; padding: 16px;
}
.card h2 { font-size: 14px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; }

.chart-container { width: 100%; height: 400px; }

.signal-row {
  display: grid; grid-template-columns: auto 1fr auto auto auto auto auto auto;
  gap: 8px; padding: 10px 0; border-bottom: 1px solid var(--border);
  font-size: 13px; align-items: center;
}
.signal-row:last-child { border-bottom: none; }
.signal-row .sym { font-weight: 700; font-size: 15px; }
.signal-row .dir.long { color: var(--green); }
.signal-row .dir.short { color: var(--red); }
.signal-row .price { font-family: 'JetBrains Mono', monospace; }
.signal-row .tp { color: var(--green); }
.signal-row .sl { color: var(--red); }
.signal-row .edge { font-weight: 600; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
.edge.high { background: #166534; color: #86efac; }
.edge.tradable { background: #1e3a5f; color: #93c5fd; }
.edge.watch { background: #422006; color: #fcd34d; }
.edge.ignore { background: #1f2937; color: #6b7280; }
.signal-row .rr { font-family: 'JetBrains Mono', monospace; color: var(--muted); }
.signal-row .time { color: var(--muted); font-size: 11px; }

.stats-grid { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 8px; }
.stat-box { text-align: center; padding: 12px; background: rgba(6, 182, 212, 0.05); border-radius: 8px; }
.stat-box .num { font-size: 24px; font-weight: 700; }
.stat-box .label { font-size: 11px; color: var(--muted); margin-top: 2px; }
.stat-box.green .num { color: var(--green); }
.stat-box.red .num { color: var(--red); }
.stat-box.blue .num { color: var(--blue); }
.stat-box.purple .num { color: var(--purple); }

.source-list { font-size: 13px; }
.source-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--border); }
.source-row:last-child { border-bottom: none; }
.source-row .bar-bg { width: 100px; height: 6px; background: #1f2937; border-radius: 3px; overflow: hidden; margin-left: 8px; }
.source-row .bar-fill { height: 100%; border-radius: 3px; }

@media (max-width: 900px) {
  .grid-2, .grid-3 { grid-template-columns: 1fr; }
  .header { flex-direction: column; gap: 8px; }
  .price-ticker { gap: 12px; }
}

.agent-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; }
.agent-item { padding: 10px; border-radius: 8px; background: rgba(6, 182, 212, 0.05); border: 1px solid var(--border); text-align: center; }
.agent-item .name { font-size: 12px; font-weight: 600; }
.agent-item .lane { font-size: 10px; color: var(--muted); }
.agent-item .status { font-size: 11px; margin-top: 4px; }
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>SYNAPSE <span>Compound</span></h1>
    <div style="font-size:11px;color:var(--muted);margin-top:2px" id="last-update">Loading...</div>
  </div>
  <div class="header-right">
    <div class="price-ticker" id="price-ticker">
      <div class="item"><span class="sym">BTC</span><span class="val" id="btc-price">--</span></div>
      <div class="item"><span class="sym">ETH</span><span class="val" id="eth-price">--</span></div>
      <div class="item"><span class="sym">SOL</span><span class="val" id="sol-price">--</span></div>
    </div>
    <div><span class="status-dot green"></span>Pipeline Active</div>
  </div>
</div>

<div class="grid grid-3" style="margin-bottom:12px">
  <div class="card">
    <h2>📊 Price Chart &mdash; <select id="chart-sym" style="background:var(--bg);color:var(--text);border:1px solid var(--border);padding:2px 6px;border-radius:4px;font-size:12px">
      <option value="BTC-USD">BTC/USD</option><option value="ETH-USD">ETH/USD</option><option value="SOL-USD">SOL/USD</option>
    </select>
    <select id="chart-range" style="background:var(--bg);color:var(--text);border:1px solid var(--border);padding:2px 6px;border-radius:4px;font-size:12px;margin-left:6px">
      <option value="1">1 Day</option><option value="3">3 Days</option><option value="7">7 Days</option>
    </select>
    </h2>
    <div class="chart-container" id="chart-container"></div>
  </div>
  <div class="card">
    <h2>⚡ Key Stats</h2>
    <div class="stats-grid" id="stats-grid">
      <div class="stat-box blue"><div class="num" id="stat-total">--</div><div class="label">Total Signals</div></div>
      <div class="stat-box green"><div class="num" id="stat-actionable">--</div><div class="label">Actionable</div></div>
      <div class="stat-box purple"><div class="num" id="stat-high">--</div><div class="label">High Conf (>0.5)</div></div>
      <div class="stat-box blue"><div class="num" id="stat-athr">--</div><div class="label">ATR (BTC)</div></div>
    </div>
    <div style="margin-top:12px">
      <h2>🤖 Agents</h2>
      <div class="agent-grid" id="agent-grid"></div>
    </div>
    <div style="margin-top:12px">
      <h2>📡 Source Health</h2>
      <div class="source-list" id="source-list"></div>
    </div>
  </div>
</div>

<div class="card" style="margin-bottom:12px">
  <h2>🔥 Trade Signals  <span style="font-weight:400;text-transform:none;font-size:12px;color:var(--muted)">— ranked by edge score</span></h2>
  <div id="signals-header" style="display:grid;grid-template-columns:auto 1fr auto auto auto auto auto auto;gap:8px;padding:6px 0;font-size:11px;color:var(--muted);text-transform:uppercase;border-bottom:1px solid var(--border)">
    <div>Dir</div><div>Signal</div><div>Entry</div><div>TP</div><div>SL</div><div>Edge</div><div>R:R</div><div>Age</div>
  </div>
  <div id="signals-list"></div>
</div>

<div style="text-align:center;padding:20px;font-size:12px;color:var(--muted)">
  Synapse Compound v0.1 — <span id="footer-time"></span>
  — <a href="#" onclick="refresh();return false" style="color:var(--accent)">Refresh</a>
</div>

<script>
let chart = null;
let currentSymbol = 'BTC-USD';
let currentDays = 1;

async function fetchData() {
  const [signalsRes, pricesRes, stateRes] = await Promise.all([
    fetch('/api/signals?min_edge=0&limit=100'),
    fetch('/api/prices'),
    fetch('/api/state'),
  ]);
  const signals = await signalsRes.json();
  const prices = await pricesRes.json();
  const state = await stateRes.json();

  // Prices
  if (prices.bitcoin) document.getElementById('btc-price').textContent = '$' + prices.bitcoin.usd.toLocaleString();
  if (prices.ethereum) document.getElementById('eth-price').textContent = '$' + prices.ethereum.usd.toLocaleString();
  if (prices.solana) document.getElementById('sol-price').textContent = '$' + prices.solana.usd.toLocaleString();
  document.getElementById('last-update').textContent = 'Updated: ' + (signals.generated_at ? new Date(signals.generated_at).toLocaleTimeString() : '--');

  // Stats
  document.getElementById('stat-total').textContent = signals.total || 0;
  document.getElementById('stat-actionable').textContent = signals.actionable || 0;
  if (signals.atr_summary) {
    document.getElementById('stat-athr').textContent = (signals.atr_summary['BTC-USD'] || signals.atr_summary['BTC'] || '--') + '%';
  }

  // Signals
  const list = document.getElementById('signals-list');
  const sigs = signals.signals || [];
  if (sigs.length === 0) {
    list.innerHTML = '<div style="padding:20px;text-align:center;color:var(--muted);font-size:13px">No trade signals yet — pipeline runs every 10 minutes</div>';
  } else {
    list.innerHTML = sigs.map(s => {
      const dirClass = (s.direction === 'LONG' || s.direction === 'UP') ? 'long' : 'short';
      const edgeClass = s.rating ? s.rating.toLowerCase() : 'ignore';
      const age = s.timestamp ? Math.floor((Date.now() - new Date(s.timestamp).getTime()) / 60000) : '?';
      return `<div class="signal-row">
        <div class="dir ${dirClass}"><strong>${s.direction === 'LONG' ? '▲' : '▼'}</strong></div>
        <div class="sym">${s.symbol}</div>
        <div class="price">$${s.entry_price?.toFixed(2)}</div>
        <div class="tp">$${s.take_profit_1?.toFixed(2)}</div>
        <div class="sl">$${s.stop_loss?.toFixed(2)}</div>
        <div class="edge ${edgeClass}">${s.edge_score}</div>
        <div class="rr">${s.risk_reward_ratio?.toFixed(2)}</div>
        <div class="time">${age}m</div>
      </div>`;
    }).join('');
  }

  // Agent state
  const agents = state.agents_active || [];
  const agentGrid = document.getElementById('agent-grid');
  if (agents.length > 0) {
    agentGrid.innerHTML = agents.map(a => {
      const lanes = {openclaw:'Builder', nemoclaw:'Builder', kairos:'Ops', hermes:'Hub', shannon:'Ref'};
      return `<div class="agent-item"><div class="name">${a}</div><div class="lane">${lanes[a]||'agent'}</div><div class="status" style="color:var(--green)">● active</div></div>`;
    }).join('');
  }
}

async function loadChart(symbol, days) {
  currentSymbol = symbol;
  currentDays = days;
  const res = await fetch(`/api/chart/${symbol}?days=${days}`);
  const data = await res.json();
  if (data.error) return;
  
  const container = document.getElementById('chart-container');
  container.innerHTML = '';
  
  chart = LightweightCharts.createChart(container, {
    layout: {
      textColor: '#64748b', background: {type: 'solid', color: '#111827'},
      fontSize: 11,
    },
    grid: {
      vertLines: {color: '#1e293b'},
      horzLines: {color: '#1e293b'},
    },
    crosshair: {mode: LightweightCharts.CrosshairMode.Normal},
    rightPriceScale: {borderColor: '#1e293b'},
    timeScale: {borderColor: '#1e293b', timeVisible: true, secondsVisible: false},
    width: container.clientWidth,
    height: 380,
  });

  const candlestickSeries = chart.addCandlestickSeries({
    upColor: '#22c55e', downColor: '#ef4444',
    borderDownColor: '#ef4444', borderUpColor: '#22c55e',
    wickDownColor: '#ef4444', wickUpColor: '#22c55e',
  });

  candlestickSeries.setData(data.candles || []);
  
  // Add volume as histogram
  const volumeSeries = chart.addHistogramSeries({
    priceFormat: {type: 'volume'},
    priceScaleId: '',
  });
  volumeSeries.setData((data.candles || []).slice(1).map((c, i) => ({
    time: c.time,
    value: Math.abs(c.close - c.open) * 10000,
    color: c.close >= c.open ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)',
  })));
  volumeSeries.priceScale().applyOptions({
    scaleMargins: {top: 0.8, bottom: 0},
  });

  chart.timeScale().fitContent();
}

function refresh() {
  fetchData();
  loadChart(currentSymbol, currentDays);
}

// Selection changes
document.getElementById('chart-sym').addEventListener('change', function() {
  loadChart(this.value, currentDays);
});
document.getElementById('chart-range').addEventListener('change', function() {
  loadChart(currentSymbol, parseInt(this.value));
});

// Resize handler
window.addEventListener('resize', () => {
  if (chart) {
    const container = document.getElementById('chart-container');
    chart.applyOptions({width: container.clientWidth});
  }
});

// Auto refresh every 30 seconds
setInterval(fetchData, 30000);
setInterval(() => document.getElementById('footer-time').textContent = new Date().toLocaleString(), 1000);

// Init
loadChart('BTC-USD', 1);
fetchData();
document.getElementById('footer-time').textContent = new Date().toLocaleString();

// Fetch Striker stats in background
fetch('/api/striker-stats').then(r => r.json()).then(data => {
  if (data.total_signals) document.getElementById('stat-high').textContent = data.high_confidence || 0;
  if (data.by_direction) {
    const dirDiv = document.createElement('div');
    dirDiv.style.cssText = 'margin-top:8px;font-size:12px';
    dirDiv.innerHTML = 'Long: ' + (data.by_direction.long||0) + ' / Short: ' + (data.by_direction.short||0) + ' / Up: ' + (data.by_direction.up||0) + ' / Down: ' + (data.by_direction.down||0);
    document.getElementById('stats-grid').after(dirDiv);
  }
  // Source health
  const srcDiv = document.getElementById('source-list');
  if (data.by_symbol) {
    const maxCount = Math.max(...Object.values(data.by_symbol));
    srcDiv.innerHTML = Object.entries(data.by_symbol).slice(0,6).map(([k,v]) => {
      const pct = (v / maxCount * 100).toFixed(0);
      const color = k.includes('BTC') ? '#f7931a' : k.includes('ETH') ? '#627eea' : '#00ffbd';
      return `<div class="source-row"><span>${k}</span><span style="display:flex;align-items:center;gap:6px">${v.toLocaleString()}<div class="bar-bg"><div class="bar-fill" style="width:${pct}%;background:${color}"></div></div></span></div>`;
    }).join('');
  }
});
</script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1", "name": "synapse-compound"}


if __name__ == "__main__":
    port = int(os.environ.get("SYNAPSE_PORT", "3333"))
    print(f" Synapse Compound Dashboard starting on http://0.0.0.0:{port}")
    print(f"   API:     http://localhost:{port}/api/signals")
    print(f"   Charts:  http://localhost:{port}/")
    print(f"   Health:  http://localhost:{port}/health")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")