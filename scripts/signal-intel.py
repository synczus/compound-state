#!/usr/bin/env python3
"""
Signal Intel — autonomous signal intelligence agent.
Queries the Striker signal DB, filters for high-confidence signals,
writes structured market insights to agentmemory and compound-state.
Posts findings to Telegram autonomously.
"""
import json
import logging
import sqlite3
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("signal-intel")

KESTREL_DIR = Path("/home/synczus/kestrel")
SIGNALS_DB = KESTREL_DIR / "kestrel_signals.db"
COMPOUND_STATE = KESTREL_DIR / "compound-state.json"
AGENTMEMORY_API = "http://localhost:3111/agentmemory"


def query_high_confidence(db_path: Path, min_conf: float = 0.2) -> list[dict]:
    """Get high-confidence market signals from the Striker database."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT id, timestamp, symbol, price, direction, confidence,
               move_pct, volume
        FROM signals
        WHERE confidence >= ?
        ORDER BY confidence DESC, id DESC
        LIMIT 50
    """, (min_conf,)).fetchall()

    conn.close()
    return [dict(r) for r in rows]


def build_insight(signals: list[dict]) -> dict:
    """Analyze signal clusters and produce structured insight."""
    if not signals:
        return {"type": "no_high_confidence_signals", "summary": "No signals above threshold"}

    by_symbol = {}
    for s in signals:
        key = f"{s['symbol']}_{s['direction']}"
        if key not in by_symbol:
            by_symbol[key] = {"symbol": s['symbol'], "direction": s['direction'],
                              "count": 0, "confidences": [], "prices": [],
                              "moves": [], "volumes": [], "latest": s['timestamp']}
        b = by_symbol[key]
        b["count"] += 1
        b["confidences"].append(s["confidence"])
        if s.get("price"):
            b["prices"].append(s["price"])
        b["moves"].append(s["move_pct"])
        b["volumes"].append(s.get("volume", 0))
        if s["timestamp"] > b["latest"]:
            b["latest"] = s["timestamp"]

    ranked = []
    for key, b in by_symbol.items():
        avg_conf = sum(b["confidences"]) / len(b["confidences"])
        avg_move = sum(b["moves"]) / len(b["moves"])
        avg_vol = sum(b["volumes"]) / len(b["volumes"]) if b["volumes"] else 0
        avg_price = sum(b["prices"]) / len(b["prices"]) if b["prices"] else 0
        score = avg_conf * b["count"]

        ranked.append({
            "symbol": b["symbol"],
            "direction": b["direction"],
            "signal_count": b["count"],
            "avg_confidence": round(avg_conf, 4),
            "avg_move_pct": round(avg_move, 3),
            "avg_price": round(avg_price, 2),
            "avg_volume": round(avg_vol, 0),
            "latest": b["latest"],
            "score": round(score, 2),
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)

    top = ranked[0] if ranked else None
    summary_parts = []
    if top:
        direction_emoji = "📈" if "up" in top["direction"] or "long" in top["direction"] else "📉"
        summary_parts.append(
            f"{direction_emoji} **{top['symbol']}** {top['direction']} "
            f"×{top['signal_count']} @ {top['avg_confidence']*100:.1f}% confidence, "
            f"avg {top['avg_move_pct']:.2f}% move"
        )

    return {
        "type": "market_insight",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_high_conf_signals": len(signals),
        "signal_clusters": len(ranked),
        "top_cluster": top,
        "ranked_clusters": ranked[:5],
        "summary": "\n".join(summary_parts) if summary_parts else "No actionable clusters",
    }


def write_to_agentmemory(insight: dict) -> bool:
    """Persist insight into agentmemory for cross-agent recall."""
    try:
        payload = json.dumps({
            "content": insight["summary"],
            "metadata": {
                "type": insight["type"],
                "generated_at": insight["generated_at"],
                "total_signals": insight["total_high_conf_signals"],
                "top_cluster": insight.get("top_cluster"),
                "source": "signal-intel",
            }
        }).encode()
        req = urllib.request.Request(
            f"{AGENTMEMORY_API}/remember",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = resp.read().decode()
            log.info("agentmemory write: %s", result[:200])
            return True
    except Exception as e:
        log.warning("agentmemory write failed: %s", e)
        return False


def update_compound_state(insight: dict) -> bool:
    """Update the compound state JSON with latest signal intelligence."""
    try:
        state = json.loads(COMPOUND_STATE.read_text())
        state["signal_intel"] = {
            "last_analysis": insight["generated_at"],
            "high_conf_signals": insight["total_high_conf_signals"],
            "top_signal": insight.get("top_cluster"),
            "summary": insight["summary"],
        }
        COMPOUND_STATE.write_text(json.dumps(state, indent=2))
        log.info("compound-state updated")
        return True
    except Exception as e:
        log.warning("compound-state update failed: %s", e)
        return False


def dispatch_to_telegram(insight: dict) -> bool:
    """Send high-signal insight to Telegram via direct bot API."""
    try:
        top = insight.get("top_cluster")
        if not top:
            return False

        # Read bot token from .env
        env_path = KESTREL_DIR / ".env"
        token = None
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("TELEGRAM_BOT_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"\'')
                    break

        if not token:
            log.warning("No TELEGRAM_BOT_TOKEN found in .env")
            return False

        direction_emoji = "📈" if "up" in top["direction"] or "long" in top["direction"] else "📉"
        text = (
            f"🤖 **Signal Intel** — Autonomous Analysis\n"
            f"{direction_emoji} **{top['symbol']} {top['direction']}**\n"
            f"• {top['signal_count']} signals @ {top['avg_confidence']*100:.1f}% avg confidence\n"
            f"• Avg move: {top['avg_move_pct']:.2f}%\n"
            f"• Avg price: ${top['avg_price']:.2f}\n"
            f"• Score: {top['score']}\n\n"
            f"_{insight['total_high_conf_signals']} high-confidence signals analyzed_"
        )

        chat_id = "-5087043705"
        api_url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = json.dumps({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }).encode()

        req = urllib.request.Request(
            api_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            log.info("Telegram dispatch: %s", result.get("ok", False))
            return result.get("ok", False)
    except Exception as e:
        log.warning("telegram dispatch failed: %s", e)
        return False


def main():
    log.info("Signal Intel — starting analysis")

    signals = query_high_confidence(SIGNALS_DB)
    log.info("Found %d high-confidence signals", len(signals))

    if len(signals) < 3:
        log.info("Not enough high-confidence signals to analyze")
        print("SILENT: insufficient signal density")
        return

    insight = build_insight(signals)
    log.info("Insight: %s", insight["summary"])

    write_to_agentmemory(insight)
    update_compound_state(insight)
    dispatch_to_telegram(insight)

    print(f"Signal Intel: {insight['summary']}")


if __name__ == "__main__":
    main()