"""
Market Striker Scoring Webhook — FastAPI Receiver

Receives TradingView webhook alerts, scores them with the scoring engine,
stores results to DuckDB, and routes high-scoring signals to Telegram.

Endpoints:
  POST /webhook/tradingview  — TradingView alert webhook
  POST /webhook/striker      — Striker internal signal webhook
  GET  /scores/latest        — Latest scored signals
  GET  /health               — Service health

Usage:
    uvicorn webhook:app --host 0.0.0.0 --port 8090
"""
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from scoring.scoring_engine import score_signal, RULES
from scoring.mtf_analyzer import analyze_mtf

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("scoring-webhook")

SCORES_DB = Path(__file__).parent / "scores.duckdb"
STRIKER_DB = Path(__file__).parent.parent / "kestrel_signals.db"

app = FastAPI(title="Market Striker Scoring", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Database ────────────────────────────────────────────────────────────────

def init_scores_db():
    """Initialize DuckDB scores table."""
    import duckdb
    con = duckdb.connect(str(SCORES_DB))
    con.execute("""
        CREATE SEQUENCE IF NOT EXISTS seq_score_id;
        CREATE TABLE IF NOT EXISTS scored_signals (
            id INTEGER DEFAULT nextval('seq_score_id'),
            timestamp TEXT,
            symbol TEXT,
            direction TEXT,
            entry_price REAL,
            take_profit REAL,
            stop_loss REAL,
            score REAL,
            action TEXT,
            breakdown_json TEXT,
            needs_llm BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.close()


def save_score(result: dict):
    """Save scored result to DuckDB."""
    import duckdb
    con = duckdb.connect(str(SCORES_DB))
    con.execute("""
        INSERT INTO scored_signals (timestamp, symbol, direction, entry_price, take_profit, stop_loss, score, action, breakdown_json, needs_llm)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        result.get("timestamp"),
        result.get("symbol"),
        result.get("direction"),
        result.get("entry_price", 0),
        result.get("take_profit", 0),
        result.get("stop_loss", 0),
        result.get("score"),
        result.get("action"),
        json.dumps(result.get("breakdown", {})),
        result.get("needs_llm", False),
    ])
    con.close()


# ── Webhook Endpoints ───────────────────────────────────────────────────────

@app.post("/webhook/tradingview")
async def tradingview_webhook(request: Request):
    """
    Receive a TradingView alert webhook.
    
    Expects JSON body with at minimum: symbol, price, direction.
    TradingView alert format via webhook:
    {
        "ticker": "BTCUSD",
        "price": 100000.0,
        "direction": "long",
        "volume": null,
        "strategy": "my_strategy_name"
    }
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Normalize TradingView alert to Striker signal format
    signal = {
        "symbol": f"{body.get('ticker', 'UNKNOWN')}-USD",
        "direction": body.get("direction", "long"),
        "entry_price": float(body.get("price", 0)),
        "take_profit": float(body.get("take_profit", 0)) or float(body.get("tp", 0)),
        "stop_loss": float(body.get("stop_loss", 0)) or float(body.get("sl", 0)),
        "confidence": float(body.get("confidence", 0.5)),
        "move_pct": float(body.get("move_pct", 0)),
        "atr_pct": float(body.get("atr_pct", 0.5)),
        "volume": float(body.get("volume", 0)) or None,
        "source": "tradingview",
        "strategy": body.get("strategy", "unknown"),
    }
    
    result = score_signal(signal)
    result["entry_price"] = signal["entry_price"]
    result["take_profit"] = signal["take_profit"]
    result["stop_loss"] = signal["stop_loss"]
    result["source"] = "tradingview"

    if result["score"] >= 40:
        try:
            mtf = analyze_mtf(signal["symbol"], signal["direction"])
            result["mtf_analysis"] = mtf
            logger.info("MTF: %s → %s (%.0f%%)", signal["symbol"],
                        mtf["verdict"]["verdict"], mtf["verdict"]["confidence"])
        except Exception as e:
            logger.warning("MTF analysis failed: %s", e)

    save_score(result)
    logger.info("TV alert: %s %s → %.1f/100 (%s)",
                signal["symbol"], signal["direction"], result["score"], result["action"])

    return result


@app.post("/webhook/striker")
async def striker_webhook(signal: dict):
    """
    Receive a Striker signal (internal HTTP or from SignalProcessor).
    Expects Striker's JSON signal format.
    """
    # Normalize Striker format if needed
    normalized = {
        "symbol": signal.get("symbol", "UNKNOWN"),
        "direction": signal.get("direction", "long"),
        "entry_price": float(signal.get("entry_price", signal.get("price", 0))),
        "take_profit": float(signal.get("take_profit", 0)),
        "stop_loss": float(signal.get("stop_loss", 0)),
        "confidence": float(signal.get("confidence", 0.5)),
        "move_pct": float(signal.get("move_pct", 0)),
        "atr_pct": float(signal.get("atr_pct", 0.5)),
        "volume": float(signal.get("volume", 0)) or None,
        "source": "striker",
    }

    result = score_signal(normalized)
    result["entry_price"] = normalized["entry_price"]
    result["take_profit"] = normalized["take_profit"]
    result["stop_loss"] = normalized["stop_loss"]
    result["source"] = "striker"

    if result["score"] >= 40:
        try:
            mtf = analyze_mtf(normalized["symbol"], normalized["direction"])
            result["mtf_analysis"] = mtf
            logger.info("MTF: %s → %s (%.0f%%)", normalized["symbol"],
                        mtf["verdict"]["verdict"], mtf["verdict"]["confidence"])
        except Exception as e:
            logger.warning("MTF analysis failed: %s", e)

    save_score(result)
    logger.info("Striker signal: %s %s → %.1f/100 (%s)",
                normalized["symbol"], normalized["direction"], result["score"], result["action"])

    return result


@app.get("/scores/latest")
async def latest_scores(limit: int = 10, action: Optional[str] = None):
    """Return the latest scored signals."""
    import duckdb
    con = duckdb.connect(str(SCORES_DB))
    try:
        query = "SELECT * FROM scored_signals"
        params = []
        if action:
            query += " WHERE action = ?"
            params.append(action)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        rows = con.execute(query, params).fetchall()
        columns = [desc[0] for desc in con.description]
        return [dict(zip(columns, row)) for row in rows]
    finally:
        con.close()


@app.get("/scores/summary")
async def scores_summary():
    """Return aggregate stats per action bucket."""
    import duckdb
    con = duckdb.connect(str(SCORES_DB))
    try:
        rows = con.execute("""
            SELECT action, COUNT(*) as count, ROUND(AVG(score), 1) as avg_score
            FROM scored_signals
            GROUP BY action
            ORDER BY avg_score DESC
        """).fetchall()
        return {"total": sum(r[1] for r in rows), "buckets": [{"action": r[0], "count": r[1], "avg_score": r[2]} for r in rows]}
    finally:
        con.close()


@app.post("/mtf/{symbol}")
async def mtf_analysis(symbol: str, direction: str = "long"):
    """Run MTF analysis on a symbol for manual lookups."""
    sym = symbol.upper() + "-USD" if "-" not in symbol else symbol.upper()
    return analyze_mtf(sym, direction)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "engine_version": RULES.get("version", "unknown"),
        "score_buckets": {k: v["action"] for k, v in RULES.get("score_buckets", {}).items()},
        "db": str(SCORES_DB),
    }


# ── Startup ────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    init_scores_db()
    logger.info("Scoring webhook ready on port 8090")


# ── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    init_scores_db()
    uvicorn.run(app, host="0.0.0.0", port=8090)