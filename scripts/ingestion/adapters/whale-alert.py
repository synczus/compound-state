#!/usr/bin/env python3
"""
Whale Alert Normalizer v0.1
Maps Whale Alert Telegram messages to event_shape format.

Output: JSON dict matching coordination.yaml event schema.
  - payload is a dict with headline, body, symbols, metrics

Usage:
  python3 scripts/ingestion/adapters/whale-alert.py < raw_message.json
"""
import hashlib
import json
import re
import sys
from datetime import datetime, timezone


def normalize(raw: dict) -> dict:
    """
    Expected raw input:
    {
        "text": "🚨 1,234 BTC ($76,543,210) transferred from Unknown Wallet to Binance",
        "message_id": "12345",
        "timestamp": "2026-06-07T12:00:00Z",
        "source": "whale-alert"
    }
    """
    text = raw.get("text", "")
    msg_id = str(raw.get("message_id", ""))
    ts = raw.get("timestamp", datetime.now(timezone.utc).isoformat())

    # Extract symbols mentioned
    symbols = list(set(re.findall(r'\b([A-Z]{2,6})\b', text)))
    noise = {"TO", "THE", "FROM", "FOR", "AND", "WAS", "HAS", "NOT",
             "YOU", "ARE", "ALL", "CAN", "ITS", "USD", "USDT", "USDC"}
    symbols = [s for s in symbols if s not in noise and len(s) > 1][:5]

    # Classify event type
    event_type = "onchain_tx"
    if any(kw in text.lower() for kw in ("burn", "destroyed")):
        event_type = "onchain_burn"
    elif any(kw in text.lower() for kw in ("mint", "issued", "created")):
        event_type = "onchain_mint"

    # Estimate magnitude from dollar amount
    amounts = re.findall(r'\$([0-9,.]+)\s*[MBT]', text)
    magnitude = 0.3  # default
    for a in amounts:
        val = float(a.replace(",", ""))
        if "B" in text and a == amounts[-1]:
            magnitude = min(val / 500_000_000_000, 1.0)  # normalize to BTC supply
        elif "M" in text and a == amounts[-1]:
            magnitude = min(val / 100_000_000, 1.0)
        elif "T" in text:
            magnitude = 0.95

    head = text[:120].replace("🚨 🚨 🚨", "").strip()

    # provenance
    canonical = f"whale-alert:{msg_id}:{ts}:{text[:200]}"
    provenance_hash = hashlib.sha256(canonical.encode()).hexdigest()[:16]

    event = {
        "source_id": "whale-alert",
        "event_type": event_type,
        "timestamp": ts,
        "payload": {
            "headline": head,
            "body": text,
            "symbols": symbols,
            "metrics": {
                "confidence": None,
                "magnitude": round(magnitude, 3),
                "velocity": "steady",
            },
        },
        "provenance_hash": provenance_hash,
    }
    return event


if __name__ == "__main__":
    raw = json.load(sys.stdin)
    event = normalize(raw)
    print(json.dumps(event, indent=2))