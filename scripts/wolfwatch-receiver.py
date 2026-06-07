"""
WolfWatch Receiver — local alert delivery bridge.
Accepts POST from kairos_monitor.py on :18790, relays to Telegram.
Stateless, single-file FastAPI app. No auth (local-only).
"""
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request

# ── Telegram dispatch ────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from signals.telegram import send_alert, format_signal
except ImportError:
    send_alert = None

EVENT_BUS = Path(__file__).resolve().parent.parent / "event-bus.md"
log = logging.getLogger("wolfwatch-receiver")
app = FastAPI(title="WolfWatch Receiver", version="1.0.0")


def log_to_event_bus(severity: str, title: str, body: str) -> None:
    """Append a timestamped line to event-bus.md."""
    try:
        ts = datetime.now(timezone.utc).isoformat()
        line = f"[{ts}] | [WOLFWATCH] | [{severity.upper()}] | {title}: {body}\n"
        with EVENT_BUS.open("a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass


@app.post("/notify")
async def notify(request: Request):
    """Receive alert from kairos_monitor.py and relay to Telegram."""
    try:
        payload = await request.json()
    except Exception:
        return {"status": "error", "detail": "invalid json"}

    source = payload.get("source", "unknown")
    severity = payload.get("severity", "info")
    title = payload.get("title", "")
    body = payload.get("body", "")
    timestamp = payload.get("timestamp", "")

    # Build Telegram message
    msg = f"<b>⬡ {title}</b>\n{body}\n<i>src: {source}</i>"

    # Dispatch
    tg_ok = False
    if send_alert:
        try:
            import asyncio
            tg_ok = await send_alert(msg)
        except Exception as e:
            log.error("Telegram send failed: %s", e)

    # Log to event-bus
    log_to_event_bus(severity, title, body)

    # Additional event-bus log for Telegram result
    if not tg_ok:
        log_to_event_bus("WARNING", f"Telegram dispatch for {title}", "failed or unconfigured")
    else:
        log_to_event_bus("INFO", f"Telegram dispatch for {title}", "sent")

    return {
        "status": "ok",
        "telegram": "sent" if tg_ok else "failed",
        "payload": payload,
    }


@app.get("/health")
async def health():
    return {"status": "ok", "service": "wolfwatch-receiver", "since": datetime.now(timezone.utc).isoformat()}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=18790, log_level="info")