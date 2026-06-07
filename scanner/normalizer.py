"""
Converts raw exchange payloads into a uniform Tick format.
Each exchange has its own field names — this is the single place that knows about them.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class Tick:
    symbol: str       # uppercase, e.g. BTCUSDT
    price: float      # last trade price
    open: float       # 24h open
    high: float       # 24h high
    low: float        # 24h low
    volume: float     # base asset volume (24h)
    timestamp: datetime
    source: str       # "binance", "bybit", etc.


def from_binance_mini_ticker(raw: dict[str, Any]) -> Tick | None:
    """
    Parse a Binance combined-stream miniTicker payload.
    Expected shape: {"stream": "btcusdt@miniTicker", "data": {...}}
    Returns None if the payload is not a miniTicker event.
    """
    data = raw.get("data", {})
    if data.get("e") != "24hrMiniTicker":
        return None
    try:
        return Tick(
            symbol=data["s"],
            price=float(data["c"]),
            open=float(data["o"]),
            high=float(data["h"]),
            low=float(data["l"]),
            volume=float(data["v"]),
            timestamp=datetime.fromtimestamp(data["E"] / 1000, tz=timezone.utc),
            source="binance",
        )
    except (KeyError, ValueError):
        return None


def from_coinbase_ticker(raw: dict[str, Any]) -> Tick | None:
    """
    Parse a Coinbase Advanced Trade ticker channel message.
    Expected shape: {"channel": "ticker", "events": [{"tickers": [...]}], "timestamp": "..."}
    Returns None if the payload is not a ticker event with data.
    """
    try:
        if raw.get("channel") != "ticker":
            return None
        events = raw.get("events", [])
        if not events:
            return None
        tickers = events[0].get("tickers", [])
        if not tickers:
            return None
        t = tickers[0]
        price = float(t["price"])
        return Tick(
            symbol=t["product_id"].replace("-", ""),   # BTC-USD → BTCUSD
            price=price,
            open=price,                                 # Coinbase basic ticker has no 24h open; approximated
            high=float(t.get("high_24h", price)),
            low=float(t.get("low_24h", price)),
            volume=float(t.get("volume_24h", 0)),
            timestamp=datetime.fromisoformat(raw["timestamp"].replace("Z", "+00:00")),
            source="coinbase",
        )
    except (KeyError, ValueError, TypeError):
        return None


def from_coinbase_pro_ticker(raw: dict[str, Any]) -> Tick | None:
    """
    Parse a Coinbase Pro/Exchange WebSocket ticker message.
    Expected shape: {"type": "ticker", "product_id": "BTC-USD", "price": "...", ...}
    Used with wss://ws-feed.pro.coinbase.com
    """
    try:
        if raw.get("type") != "ticker":
            return None
        price = float(raw["price"])
        return Tick(
            symbol=raw["product_id"].replace("-", ""),
            price=price,
            open=float(raw.get("open_24h", price)),
            high=float(raw.get("high_24h", price)),
            low=float(raw.get("low_24h", price)),
            volume=float(raw.get("volume_24h", raw.get("volume", 0))),
            timestamp=datetime.now(timezone.utc),
            source="coinbase",
        )
    except (KeyError, ValueError, TypeError):
        return None
