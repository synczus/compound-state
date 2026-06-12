#!/usr/bin/env python3
"""
Disclose.tv Normalizer v0.1
Maps Disclose.tv Telegram posts to event_shape format.

Output: JSON dict matching coordination.yaml event schema.
  - payload is a dict with headline, body, symbols, metrics

Usage:
  python3 scripts/ingestion/adapters/disclosetv.py < raw_post.json
"""
import hashlib
import json
import re
import sys
from datetime import datetime, timezone


# Cheap geopolitical keyword classifier
_GEOPOLITICAL_KW = {
    "war": ("geopolitical_conflict", 0.45),
    "sanction": ("geopolitical_sanction", 0.35),
    "crisis": ("economic_crisis", 0.35),
    "invasion": ("geopolitical_conflict", 0.5),
    "military": ("geopolitical_conflict", 0.3),
    "nuclear": ("geopolitical_conflict", 0.55),
    "embargo": ("geopolitical_sanction", 0.3),
    "treaty": ("geopolitical_diplomacy", 0.2),
    "election": ("geopolitical_politics", 0.15),
    "bank run": ("financial_crisis", 0.4),
    "debt": ("economic_crisis", 0.2),
    "inflation": ("economic_metric", 0.25),
    "interest rate": ("economic_policy", 0.25),
    "fed": ("economic_policy", 0.25),
    "collapse": ("financial_crisis", 0.4),
    "default": ("financial_crisis", 0.35),
    "bailout": ("financial_crisis", 0.3),
    "black swan": ("financial_crisis", 0.5),
    "delisting": ("market_event", 0.3),
    "raises": ("economic_policy", 0.2),
    "cpi": ("economic_metric", 0.25),
    "gdp": ("economic_metric", 0.2),
    "jobs report": ("economic_metric", 0.25),
    "bitcoin": ("crypto", 0.2),
    # Niche gem keywords
    "liquidation": ("market_event", 0.35),
    "margin call": ("financial_crisis", 0.4),
    "counterparty": ("financial_crisis", 0.3),
    "depeg": ("crypto", 0.35),
    "etf": ("market_event", 0.25),
    "sec": ("regulatory", 0.25),
    "cfpb": ("regulatory", 0.2),
}


def classify(text: str) -> tuple[str, float]:
    """Return (event_type, magnitude_boost) based on keyword match."""
    lower = text.lower()
    best_type = "news_general"
    best_boost = 0.0

    for kw, (etype, boost) in _GEOPOLITICAL_KW.items():
        if kw in lower and boost > best_boost:
            best_type = etype
            best_boost = boost

    return best_type, best_boost


def normalize(raw: dict) -> dict:
    """
    Expected raw input:
    {
        "text": "BREAKING: ECB raises interest rates by 50bp...",
        "message_id": "67890",
        "timestamp": "2026-06-07T14:00:00Z",
        "reactions": {"🔥": 42, "👍": 15},
        "source": "disclosetv"
    }
    """
    text = raw.get("text", "")
    msg_id = str(raw.get("message_id", ""))
    ts = raw.get("timestamp", datetime.now(timezone.utc).isoformat())
    reactions = raw.get("reactions", {})

    event_type, kw_mag = classify(text)

    # Symbols from currency/crypto codes
    symbols = list(set(re.findall(r'\b([A-Z]{3,5})\b', text)))
    noise = {"THE", "FOR", "AND", "WAS", "HAS", "NOT", "YOU", "ARE",
             "ALL", "CAN", "ITS", "FROM", "THAT", "THIS", "WITH",
             "WILL", "HAVE", "BEEN", "SAID", "NEWS", "JUST", "NOW"}
    symbols = [s for s in symbols if s not in noise and len(s) > 1][:5]

    # Reaction energy as velocity signal
    total_reactions = sum(reactions.values())
    if total_reactions > 50:
        velocity = "rising"
    elif total_reactions > 10:
        velocity = "steady"
    else:
        velocity = "steady"

    # Magnitude: keyword boost + reaction scale
    magnitude = min(kw_mag + (total_reactions / 200), 1.0)

    # First 200 chars as headline
    head = text[:200].strip()

    # provenance
    canonical = f"disclosetv:{msg_id}:{ts}:{text[:200]}"
    provenance_hash = hashlib.sha256(canonical.encode()).hexdigest()[:16]

    event = {
        "source_id": "disclosetv",
        "event_type": event_type,
        "timestamp": ts,
        "payload": {
            "headline": head,
            "body": text,
            "symbols": symbols,
            "metrics": {
                "confidence": None,
                "magnitude": round(magnitude, 3),
                "velocity": velocity,
            },
        },
        "provenance_hash": provenance_hash,
    }
    return event


if __name__ == "__main__":
    raw = json.load(sys.stdin)
    event = normalize(raw)
    print(json.dumps(event, indent=2))