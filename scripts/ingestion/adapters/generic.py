#!/usr/bin/env python3
"""
Generic News Adapter v0.1
Catches any Telegram channel not covered by a specific adapter.
Handles Cointelegraph, CoinDesk, CryptoQuant, Glassnode, Wu Blockchain,
Bloomberg, TechCrunch, The Econgram, PureSignal Lab, Binance Killers,
Crypto Goodreads, DiamondCrab, unfolded, and any other news channel.

Output: JSON dict matching coordination.yaml event schema.
  - payload is a dict with headline, body, symbols, metrics
  - source_id derived from channel name

Usage:
  python3 scripts/ingestion/adapters/generic.py < raw_post.json
"""
import hashlib
import json
import re
import sys
from datetime import datetime, timezone


# Source-specific baseline overrides
SOURCE_BASELINES = {
    "cointelegraph": 0.15,
    "coindesk": 0.15,
    "bloomberg": 0.25,
    "the econgram": 0.25,
    "techcrunch": 0.10,
    "cryptoquant": 0.40,      # on-chain data = higher baseline
    "glassnode": 0.40,         # on-chain data = higher baseline
    "wu blockchain": 0.30,     # crypto news with Chinese market angle
    "binance killers": 0.20,
    "crypto goodreads": 0.15,
    "diamondcrab": 0.20,
    "unfolded": 0.20,
    "puresignal lab": 0.30,
    "bcn startup club": 0.15,
    "evening trader": 0.15,
    "crypto miami": 0.10,
    "default": 0.15,
}

# Event type keywords with magnitude boost
_EVENT_TYPE_KW = {
    "bitcoin etf": ("market_institutional", 0.3),
    "spot etf": ("market_institutional", 0.3),
    "inflow": ("market_flow", 0.15),
    "outflow": ("market_flow", 0.15),
    "all-time high": ("market_milestone", 0.35),
    "ath": ("market_milestone", 0.35),
    "new low": ("market_milestone", 0.3),
    "liquidation": ("market_event", 0.4),
    "margin call": ("market_crisis", 0.45),
    "bank run": ("market_crisis", 0.5),
    "hack": ("market_incident", 0.55),
    "exploit": ("market_incident", 0.5),
    "regulation": ("regulatory", 0.25),
    "sec": ("regulatory", 0.3),
    "cfpb": ("regulatory", 0.25),
    "fdic": ("regulatory", 0.3),
    "delisting": ("market_event", 0.3),
    "depeg": ("crypto_incident", 0.4),
    "launch": ("market_launch", 0.15),
    "ipo": ("market_launch", 0.2),
    "merger": ("market_corporate", 0.2),
    "acquisition": ("market_corporate", 0.25),
    "interest rate": ("macro_policy", 0.3),
    "cpi": ("macro_metric", 0.25),
    "jobs report": ("macro_metric", 0.25),
    "gdp": ("macro_metric", 0.2),
    "inflation": ("macro_metric", 0.25),
    "recession": ("macro_metric", 0.35),
    "supply": ("crypto_metric", 0.15),
    "halving": ("crypto_metric", 0.3),
    "mining": ("crypto_mining", 0.15),
    "stake": ("crypto_staking", 0.15),
    "yield": ("defi_metric", 0.15),
    "defi": ("defi_metric", 0.15),
    "nft": ("nft_market", 0.1),
    "tokenize": ("market_institutional", 0.2),
    "blackrock": ("market_institutional", 0.25),
    "fidelity": ("market_institutional", 0.2),
    "grayscale": ("market_institutional", 0.2),
}

# Exchange/crypto symbols to extract
_SYMBOL_PATTERN = re.compile(r'\b([A-Z]{2,6})\b')
_SYMBOL_NOISE = {"THE", "FOR", "AND", "WAS", "HAS", "NOT", "YOU", "ARE",
                 "ALL", "CAN", "ITS", "FROM", "THAT", "THIS", "WITH",
                 "WILL", "HAVE", "BEEN", "SAID", "NEWS", "JUST", "NOW",
                 "BTC", "ETH", "USD", "USDT", "USDC", "SOL", "XRP", "ADA",
                 "DOT", "LINK", "AVAX", "MATIC", "ATOM", "UNI", "AAVE",
                 "LTC", "BCH", "DOGE", "SHIB", "TRX", "BNB", "EUR", "GBP",
                 "JPY", "CNY", "AUD", "CAD", "CHF", "NZD", "HKD", "SGD",
                 "KRW", "INR", "BRL", "MXN", "SEK", "NOK", "DKK", "PLN",
                 "TRY", "ZAR", "TWD", "MYR", "THB", "IDR", "PHP", "VND",
                 "EGP", "NGN", "COP", "CLP", "PEN", "QAR", "SAR", "AED"}


def detect_source(text: str, from_name: str = "") -> str:
    """Detect source_id from text content or explicit from_name."""
    name = from_name.lower().strip()
    lower = text.lower()

    # Check explicit source name first
    for source_id in SOURCE_BASELINES:
        if source_id in name or source_id in lower:
            return source_id

    # Generic fallbacks based on content patterns
    if any(kw in lower for kw in ("coinbase", "binance", "kraken", "bitfinex")):
        return "crypto_exchange"
    if any(kw in lower for kw in ("sec", "cfpb", "fdic", "regulation", "dodd-frank")):
        return "regulatory"
    return "default"


def classify(text: str) -> tuple[str, float]:
    """Return (event_type, magnitude_boost) based on keyword match."""
    lower = text.lower()
    best_type = "news_general"
    best_boost = 0.0

    for kw, (etype, boost) in _EVENT_TYPE_KW.items():
        if kw in lower and boost > best_boost:
            best_type = etype
            best_boost = boost

    return best_type, best_boost


def normalize(raw: dict) -> dict:
    """
    Expected raw input:
    {
        "text": "Bitcoin ETFs saw net outflows of $2.4 billion in May...",
        "message_id": "12345",
        "timestamp": "2026-06-07T12:00:00Z",
        "source": "cointelegraph"
    }
    """
    text = raw.get("text", "")
    msg_id = str(raw.get("message_id", ""))
    ts = raw.get("timestamp", datetime.now(timezone.utc).isoformat())
    from_name = raw.get("source", "")

    source_id = detect_source(text, from_name)
    event_type, mag_boost = classify(text)

    # Extract symbols
    symbols = list(set(_SYMBOL_PATTERN.findall(text)))
    symbols = [s for s in symbols if s not in _SYMBOL_NOISE and len(s) > 1][:5]

    # Velocity from urgency keywords
    velocity = "steady"
    urgency_kw = ("breaking", "just in", "new", "now", "urgent", "🚨", "flash")
    if any(kw in text.lower()[:80] for kw in urgency_kw):
        velocity = "rising"

    # Magnitude: keyword boost + a small text-length bonus
    magnitude = min(mag_boost + (len(text) / 2000), 1.0)

    # First 200 chars as headline
    head = text[:200].strip()

    # provenance
    canonical = f"{source_id}:{msg_id}:{ts}:{text[:200]}"
    provenance_hash = hashlib.sha256(canonical.encode()).hexdigest()[:16]

    event = {
        "source_id": source_id,
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