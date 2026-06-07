"""
Kestrel Striker — Live Market Scanner & Signal Engine

Connects to Coinbase Advanced Trade WebSocket, monitors BTC-USD/ETH-USD/SOL-USD
for price moves exceeding threshold, emits structured signals, auto-reconnects
on network loss with exponential backoff.

Designed for systemd Restart=always: exits cleanly on SIGTERM, rapid restart safe.
"""
import asyncio
import fcntl
import json
import logging
import os
import signal
import sqlite3
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# systemd launches this file as `python core/main.py`; make package imports
# resolve the same way they do under `python -m core.main`.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import websockets

from core.config import (
    COINBASE_WS_URL,
    SCAN_SYMBOLS,
    PRICE_MOVE_THRESHOLD,
    QUEUE_MAX_SIZE,
)

logger = logging.getLogger("striker")
SIGNALS_DB = Path(__file__).parent.parent / "kestrel_signals.db"
HEALTH_FILE = Path(__file__).parent.parent / "striker_health.json"
LOCK_FILE = Path("/tmp/kestrel-striker-core.lock")
_LOCK_HANDLE = None


# ── Data Model ──────────────────────────────────────────────────────────────

@dataclass(slots=True)
class Signal:
    """A single structured signal emitted by Striker."""
    timestamp: str
    symbol: str
    price: float
    direction: str       # "long" | "short"
    confidence: float    # 0.0–1.0
    move_pct: float
    volume: Optional[float] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    def to_db_tuple(self) -> tuple:
        return (self.timestamp, self.symbol, self.price, self.direction,
                self.confidence, self.move_pct, self.volume)


# ── Signal Store ────────────────────────────────────────────────────────────

def init_db() -> None:
    """Create the signals table if it doesn't exist."""
    conn = sqlite3.connect(str(SIGNALS_DB))
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                direction TEXT NOT NULL,
                confidence REAL NOT NULL,
                move_pct REAL NOT NULL,
                volume REAL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_signals_ts ON signals(timestamp)
        """)
        conn.commit()
    finally:
        conn.close()


def write_signal(signal: Signal) -> None:
    """Write a signal to SQLite."""
    conn = sqlite3.connect(str(SIGNALS_DB))
    try:
        conn.execute(
            "INSERT INTO signals (timestamp, symbol, price, direction, confidence, move_pct, volume) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            signal.to_db_tuple(),
        )
        conn.commit()
    finally:
        conn.close()


def signal_count() -> int:
    """Return total signals in DB."""
    conn = sqlite3.connect(str(SIGNALS_DB))
    try:
        row = conn.execute("SELECT COUNT(*) FROM signals").fetchone()
        return row[0] if row else 0
    finally:
        conn.close()


# ── Single Instance Guard ───────────────────────────────────────────────────

def acquire_single_instance_lock() -> bool:
    """Prevent duplicate Striker scanners from writing competing health/DB state."""
    global _LOCK_HANDLE
    _LOCK_HANDLE = LOCK_FILE.open("a+")
    try:
        fcntl.flock(_LOCK_HANDLE, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        logger.error("another Striker instance already holds %s", LOCK_FILE)
        return False
    _LOCK_HANDLE.seek(0)
    _LOCK_HANDLE.truncate()
    _LOCK_HANDLE.write(str(os.getpid()))
    _LOCK_HANDLE.flush()
    return True


# ── Health ──────────────────────────────────────────────────────────────────

def write_health(state: dict) -> None:
    """Persist current health state for external health checks."""
    try:
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        tmp_file = HEALTH_FILE.with_suffix(HEALTH_FILE.suffix + ".tmp")
        tmp_file.write_text(json.dumps(state, indent=2))
        os.replace(tmp_file, HEALTH_FILE)
    except Exception:
        pass


# ── Price Tracker ───────────────────────────────────────────────────────────

@dataclass(slots=True)
class PriceTracker:
    """
    Tracks prices for signal detection using a trailing 5-minute window.
    
    Emits a signal when the current price deviates >threshold from the
    window anchor (first tick seen in each 5-minute epoch). This avoids
    the "last-tick vs this-tick" problem where consecutive ticks are
    milliseconds apart and barely move.
    """
    _prices: dict[str, dict] = field(default_factory=dict)
    _window_anchor: dict[str, dict] = field(default_factory=dict)  # symbol -> {price, epoch_start}
    WINDOW_SECONDS: int = 300  # 5 minutes
    MIN_WINDOW_TICKS: int = 3
    _tick_counts: dict[str, int] = field(default_factory=dict)

    def seed(self, symbol: str, price: float, volume: Optional[float] = None) -> None:
        """Seed initial price and start the first window."""
        now = time.time()
        self._prices[symbol] = {"price": price, "volume": volume}
        self._window_anchor[symbol] = {"price": price, "epoch_start": now, "volume": volume}
        self._tick_counts[symbol] = 0

    def _get_window_anchor(self, symbol: str, now: float, price: float, volume: Optional[float] = None) -> None:
        """Return or reset the anchor for the current 5-minute window."""
        anchor = self._window_anchor.get(symbol)
        if anchor is None or (now - anchor["epoch_start"]) >= self.WINDOW_SECONDS:
            # Start a new window
            self._window_anchor[symbol] = {"price": price, "epoch_start": now, "volume": volume}
            self._tick_counts[symbol] = 0

    def update(self, symbol: str, price: float, volume: Optional[float] = None) -> Optional[Signal]:
        """
        Ingest a new price tick. Returns a Signal if the move exceeds threshold
        relative to the 5-minute trailing window anchor.
        """
        now = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()
        prev = self._prices.get(symbol)

        if prev is None:
            # First tick — seed and wait for a window
            self.seed(symbol, price, volume)
            return None

        # Update last-tick tracker (used only for seeding, not signal comparison)
        self._prices[symbol] = {"price": price, "volume": volume or prev.get("volume")}

        # Refresh or create window anchor
        anchor = self._window_anchor.get(symbol)
        if anchor is None or (now - anchor["epoch_start"]) >= self.WINDOW_SECONDS:
            anchor = {"price": price, "epoch_start": now, "volume": volume}
            self._window_anchor[symbol] = anchor
            self._tick_counts[symbol] = 0

        self._tick_counts[symbol] = self._tick_counts.get(symbol, 0) + 1

        # Only evaluate after we have enough ticks in this window
        if self._tick_counts[symbol] < self.MIN_WINDOW_TICKS:
            return None

        anchor_price = anchor["price"]
        if anchor_price == 0:
            return None

        move_pct = ((price - anchor_price) / anchor_price) * 100.0

        if abs(move_pct) >= PRICE_MOVE_THRESHOLD:
            direction = "long" if move_pct > 0 else "short"
            confidence = min(abs(move_pct) / 5.0, 1.0)  # 5% move = full confidence
            logger.info("SIGNAL: %s vs anchor %.2f (%.4f%% move in %.0fs window)",
                        symbol, anchor_price, move_pct, now - anchor["epoch_start"])
            sig = Signal(
                timestamp=now_iso,
                symbol=symbol,
                price=price,
                direction=direction,
                confidence=round(confidence, 4),
                move_pct=round(move_pct, 4),
                volume=volume or anchor.get("volume"),
            )
            return sig

        return None


# ── WebSocket Client ────────────────────────────────────────────────────────

class StrikerClient:
    """Async WebSocket client for Coinbase market data."""

    def __init__(self) -> None:
        self.tracker = PriceTracker()
        self._running = True
        self._connected_since: Optional[str] = None
        self._signals_this_session = 0
        self._total_signals = 0

    async def _subscribe(self, ws) -> None:
        """Send the subscription message for all configured symbols."""
        channel = "ticker"  # Coinbase ticker channel sends real-time price updates
        product_ids = SCAN_SYMBOLS
        subscribe_msg = {
            "type": "subscribe",
            "product_ids": product_ids,
            "channel": channel,
        }
        await ws.send(json.dumps(subscribe_msg))
        logger.info("subscribed to %s on %s for %s", channel, COINBASE_WS_URL, product_ids)

    async def _handle_message(self, raw: str) -> None:
        """Route an incoming websocket message using Coinbase Advanced Trade format."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("unparseable message: %.120s", raw)
            return

        channel = data.get("channel", "")
        events = data.get("events", [])

        if channel == "ticker":
            for event in events:
                event_type = event.get("type", "")
                tickers = event.get("tickers", [])
                for ticker in tickers:
                    product_id = ticker.get("product_id", "")
                    price_str = ticker.get("price", "")
                    volume_str = ticker.get("volume_24_h")

                    if not price_str:
                        continue

                    try:
                        price = float(price_str)
                    except (ValueError, TypeError):
                        continue

                    volume = float(volume_str) if volume_str else None

                    if event_type == "snapshot":
                        # Seed the price tracker with initial price — no signal
                        self.tracker.seed(product_id, price, volume)
                        logger.debug("seeded %s @ %.2f", product_id, price)
                    elif event_type == "update":
                        signal = self.tracker.update(product_id, price, volume)
                        if signal:
                            self._signals_this_session += 1
                            self._total_signals += 1
                            write_signal(signal)
                            logger.info("SIGNAL: %s %s @ %.2f (%.2f%%)",
                                        signal.symbol, signal.direction.upper(),
                                        signal.price, signal.move_pct)
                            print(signal.to_json(), flush=True)

        elif channel == "subscriptions":
            logger.info("subscription confirmed: %s", data.get("events", []))
        elif channel == "heartbeats":
            pass  # silent — Coinbase sends regular heartbeats
        else:
            logger.debug("unhandled channel: %s", channel)

    async def _health_tick(self) -> None:
        """Periodically refresh the health file with current state."""
        while self._running:
            await asyncio.sleep(60)
            write_health({
                "status": "connected" if self._connected_since else "disconnected",
                "connected_since": self._connected_since,
                "signals_this_session": self._signals_this_session,
                "total_signals": signal_count(),
            })

    async def connect(self) -> None:
        """Main connect-reconnect loop."""
        backoff = 1  # seconds

        # Start periodic health refresh in background
        asyncio.create_task(self._health_tick())

        while self._running:
            self._connected_since = None
            try:
                logger.info("connecting to %s", COINBASE_WS_URL)
                async with websockets.connect(
                    COINBASE_WS_URL,
                    ping_interval=20,
                    ping_timeout=10,
                    max_size=2 ** 20,  # 1 MB
                ) as ws:
                    logger.info("connected")
                    self._connected_since = datetime.now(timezone.utc).isoformat()
                    backoff = 1  # reset on successful connect
                    write_health({
                        "status": "connected",
                        "connected_since": self._connected_since,
                        "signals_this_session": self._signals_this_session,
                        "total_signals": signal_count(),
                    })

                    await self._subscribe(ws)

                    async for message in ws:
                        await self._handle_message(message)

            except websockets.ConnectionClosed:
                logger.warning("connection closed (reconnecting in %ds)", backoff)
            except asyncio.TimeoutError:
                logger.warning("timeout (reconnecting in %ds)", backoff)
            except OSError as exc:
                logger.error("network error: %s (reconnect in %ds)", exc, backoff)

            # Write health as disconnected
            write_health({
                "status": "disconnected",
                "connected_since": None,
                "signals_this_session": self._signals_this_session,
                "total_signals": signal_count(),
            })

            if not self._running:
                break

            # Exponential backoff, cap at 30s
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)

    def stop(self) -> None:
        """Signal graceful shutdown."""
        self._running = False


# ── Entry Point ─────────────────────────────────────────────────────────────

async def main():
    # Setup logging to stderr (stdout reserved for signal JSON)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )

    logger.info("Kestrel Striker starting — symbols=%s, threshold=%.1f%%",
                SCAN_SYMBOLS, PRICE_MOVE_THRESHOLD)

    if not acquire_single_instance_lock():
        return 2

    # Init DB schema
    init_db()

    client = StrikerClient()

    # Wire up signal handling for systemd's SIGTERM
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, client.stop)

    try:
        await client.connect()
    except asyncio.CancelledError:
        client.stop()
    finally:
        total = signal_count()
        logger.info("Striker stopping — emitted %d signals this session, %d total in DB",
                    client._signals_this_session, total)
        write_health({
            "status": "stopped",
            "connected_since": None,
            "signals_this_session": client._signals_this_session,
            "total_signals": total,
        })


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
