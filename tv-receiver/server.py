"""
TradingView Webhook Receiver — FastAPI server on :18900.
Receives TradingView alerts, scores them through the 100-point engine,
stores in DuckDB, dispatches to Telegram and agentmemory on threshold.
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request

from scorer import ScoringEngine
from store import SignalStore

log = logging.getLogger("tv-receiver")
app = FastAPI(title="TradingView Signal Receiver", version="1.0.0")

# ── Paths ──────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent
CONFIG_PATH = BASE / "config.json"

# ── Init ───────────────────────────────────────────────────────────────
with open(CONFIG_PATH) as f:
    cfg = json.load(f)

engine = ScoringEngine(CONFIG_PATH)
store = SignalStore()

# ── Telegram dispatch ──────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = None
env_path = BASE.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            TELEGRAM_BOT_TOKEN = line.split("=", 1)[1].strip().strip('"\'')
            log.info("Loaded TELEGRAM_BOT_TOKEN from .env")
            break
import urllib.request


def send_telegram(result: dict) -> bool:
    """Send scored signal to Telegram if above threshold."""
    if not TELEGRAM_BOT_TOKEN:
        return False
    tg = cfg.get("telegram", {})
    if not tg.get("enabled", True):
        return False
    if result["score"] < tg.get("min_score_to_alert", 40):
        return False

    s = result["signal"]
    bk = result.get("breakdown", {})
    bucket = cfg["action_buckets"].get(result["bucket"], {})
    emoji = bucket.get("emoji", "📊")

    text = (
        f"{emoji} **Scored Signal** | {s['symbol']} {s['direction'].upper()}\n"
        f"• Score: {result['score']}/100 → **{result['bucket'].upper()}**\n"
        f"• Price: ${s['price']:.2f}\n"
        f"• Trend: {s['trend']*100:.0f}% | Vol: {s['volume_expansion']*100:.0f}%\n"
        f"• Breakdown: T{bk['trend_regime']:.0f}/40 | V{bk['volume_liquidity']:.0f}/25 | "
        f"S{bk['setup_quality']:.0f}/20 | M{bk['timeframe_alignment']:.0f}/10 | F{bk['freshness']:.0f}/5\n"
        f"_{bucket.get('description', '')}_"
    )

    try:
        api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = json.dumps({
            "chat_id": tg.get("chat_id", "-5087043705"),
            "text": text,
            "parse_mode": "Markdown",
        }).encode()
        req = urllib.request.Request(api_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            log.info("Telegram: score %s to %s", result["score"], result["bucket"])
            return True
    except Exception as e:
        log.warning("Telegram failed: %s", e)
        return False


def send_agentmemory(result: dict) -> bool:
    """Store scored signal into agentmemory for cross-agent recall."""
    am = cfg.get("agentmemory", {})
    if not am.get("enabled", True):
        return False
    if result["score"] < am.get("min_score_to_store", 40):
        return False

    s = result["signal"]
    try:
        payload = json.dumps({
            "content": f"{result['bucket'].upper()} | {s['symbol']} {s['direction']} @ {result['score']}/100",
            "metadata": {
                "type": "scored_signal",
                "bucket": result["bucket"],
                "score": result["score"],
                "symbol": s["symbol"],
                "direction": s["direction"],
                "price": s["price"],
                "source": "tv-receiver",
            }
        }).encode()
        api = am.get("api_url", "http://localhost:3111/agentmemory")
        req = urllib.request.Request(
            f"{api}/remember",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5):
            return True
    except Exception as e:
        log.warning("agentmemory failed: %s", e)
        return False


# ── Endpoints ──────────────────────────────────────────────────────────


@app.post("/webhook/tradingview")
async def webhook(request: Request):
    """Receive TradingView alert, score it, store it, route it."""
    try:
        payload = await request.json()
    except Exception:
        return {"status": "error", "detail": "invalid json"}

    # Run MTF analysis to enrich the payload with real market context
    try:
        from mtf import enrich_scoring_payload
        payload = enrich_scoring_payload(payload)
    except Exception as e:
        log.warning("MTF enrichment failed (non-fatal): %s", e)

    result = engine.score(payload)

    if "error" in result:
        log.warning("Scoring error: %s", result["error"])
        return {"status": "error", "detail": result["error"]}

    # Attach MTF context to the result for downstream use
    mtf_data = payload.get("_mtf")
    if mtf_data:
        result["mtf"] = mtf_data
        result["signal"]["trend_alignment"] = mtf_data.get("composite_trend", result["signal"].get("trend", 0.5))
        result["signal"]["volatility"] = mtf_data.get("timeframes", {}).get("1d", {}).get("volatility", 0.5)

    sid = store.store(result)
    result["db_id"] = sid
    result["bk"] = result["breakdown"]

    # Dispatch to Telegram + agentmemory (non-blocking fire)
    try:
        import asyncio
        asyncio.create_task(_dispatch(result))
    except Exception:
        pass

    log.info("Scored %s %s: %d/100 -> %s (id=%s)",
             result["signal"]["symbol"],
             result["signal"]["direction"],
             result["score"],
             result["bucket"],
             sid)

    return {
        "status": "ok",
        "score": result["score"],
        "bucket": result["bucket"],
        "id": sid,
        "breakdown": result["breakdown"],
    }


async def _dispatch(result: dict):
    send_telegram(result)
    send_agentmemory(result)


@app.get("/health")
async def health():
    stats = store.stats()
    return {
        "status": "ok",
        "service": "tv-receiver",
        "signals_scored": stats["total"],
        "avg_score": stats["avg_score"],
        "by_bucket": stats["by_bucket"],
    }


@app.get("/signals/recent")
async def recent(limit: int = 10, min_score: float = 0):
    rows = store.recent(limit=limit, min_score=min_score)
    return {"signals": rows, "count": len(rows)}


@app.get("/signals/stats")
async def stats():
    return store.stats()


# ── Main ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    svr = cfg.get("server", {})
    host = svr.get("host", "127.0.0.1")
    port = svr.get("port", 18900)
    log.info("Starting TV Receiver on %s:%d", host, port)
    uvicorn.run(app, host=host, port=port, log_level="info")