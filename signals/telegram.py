"""
Kestrel alert formatter and Telegram dispatcher.
Uses plain httpx — no telegram library dependency.
"""
import logging

import httpx

from core.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger("kestrel.telegram")

_BASE = "https://api.telegram.org"
_TIMEOUT = 10.0


async def send_alert(message: str) -> bool:
    """
    Send *message* to the configured Telegram chat.
    Returns True on success, False on failure (logs the error, does not raise).
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured — alert suppressed: %s", message[:80])
        return False

    url = f"{_BASE}/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
        return True
    except httpx.HTTPStatusError as e:
        logger.error("Telegram HTTP %s: %s", e.response.status_code, e.response.text[:200])
    except Exception as e:
        logger.error("Telegram send failed: %s", e)
    return False


def format_signal(symbol: str, price: float, open_price: float, move_pct: float, direction: str) -> str:
    arrow = "UP" if direction == "up" else "DOWN"
    return (
        f"<b>KESTREL SIGNAL [{arrow}]</b>\n"
        f"Symbol: <code>{symbol}</code>\n"
        f"Price:  <code>${price:,.2f}</code>\n"
        f"Open:   <code>${open_price:,.2f}</code>\n"
        f"Move:   <code>{move_pct:+.2f}%</code>"
    )
