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
    """A single structured trade signal emitted by Striker.
    
    Includes entry price, take-profit, and stop-loss levels
    calculated from recent volatility (ATR) in the detection window.
    """
    timestamp: str
    symbol: str
    direction: str       # "long" | "short"
    entry_price: float   # The price that triggered the signal
    take_profit: float   # Target exit for profit
    stop_loss: float     # Target exit for loss
    confidence: float    # 0.0–1.0
    move_pct: float      # % move vs window anchor
    volume: Optional[float] = None
    atr_pct: Optional[float] = None  # Volatility measure (high-low range %)
    price: Optional[float] = None   # Kept for backwards-compatible DB writes

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    def to_db_tuple(self) -> tuple:
        return (self.timestamp, self.symbol, self.direction,
                self.entry_price, self.take_profit, self.stop_loss,
                self.confidence, self.move_pct, self.volume, self.atr_pct)


# ── Database ────────────────────────────────────────────────────────────────

def init_db() -> None:
    """Create or recreate the signals table with trade-ready columns.
    
    Migrates the old schema (price column, no TP/SL) to the new schema
    (entry_price, take_profit, stop_loss, atr_pct) by recreating the table
    via a temp table. Loses the old price column but preserves all rows.
    """
    conn = sqlite3.connect(str(SIGNALS_DB))
    try:
        old_cols = conn.execute("PRAGMA table_info(signals)").fetchall()
        if old_cols:
            col_names = [c[1] for c in old_cols]
            # Check if already migrated
            if "entry_price" in col_names and "take_profit" in col_names and "stop_loss" in col_names:
                # Drop the orphan table if it survived a previous crash
                conn.execute("DROP TABLE IF EXISTS signals_v2")
                # Check if the old "price" column is still NOT NULL — if yes, 
                # old schema needs full table recreate
                price_col = [c for c in old_cols if c[1] == "price"]
                if price_col and price_col[0][3] != 0:  # notnull flag
                    logger.info("Old schema detected (price NOT NULL). Recreating table.")
                    conn.executescript("""
                        DROP TABLE IF EXISTS signals_v2;
                        CREATE TABLE signals_v3 (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp TEXT NOT NULL,
                            symbol TEXT NOT NULL,
                            direction TEXT DEFAULT '',
                            entry_price REAL DEFAULT 0.0,
                            take_profit REAL DEFAULT 0.0,
                            stop_loss REAL DEFAULT 0.0,
                            confidence REAL DEFAULT 0.0,
                            move_pct REAL DEFAULT 0.0,
                            volume REAL,
                            atr_pct REAL
                        );
                        INSERT INTO signals_v3 (id, timestamp, symbol, direction, entry_price, confidence, move_pct, volume)
                            SELECT id, timestamp, symbol,
                                COALESCE(direction, ''),
                                COALESCE(entry_price, price, 0.0),
                                COALESCE(confidence, 0.0),
                                COALESCE(move_pct, 0.0),
                                volume
                            FROM signals;
                        DROP TABLE IF EXISTS signals;
                        ALTER TABLE signals_v3 RENAME TO signals;
                        CREATE INDEX IF NOT EXISTS idx_signals_ts ON signals(timestamp);
                    """)
                    count = conn.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
                    logger.info("Full migration complete — %d old signals preserved", count)
                else:
                    logger.info("Schema already clean — no migration needed")
            else:
                # Partial migration — columns missing. Full recreate.
                logger.info("Partial schema detected. Running full recreate.")
                conn.executescript("""
                    DROP TABLE IF EXISTS signals_v2;
                    CREATE TABLE signals_v3 (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        direction TEXT DEFAULT '',
                        entry_price REAL DEFAULT 0.0,
                        take_profit REAL DEFAULT 0.0,
                        stop_loss REAL DEFAULT 0.0,
                        confidence REAL DEFAULT 0.0,
                        move_pct REAL DEFAULT 0.0,
                        volume REAL,
                        atr_pct REAL
                    );
                    INSERT INTO signals_v3 (id, timestamp, symbol, direction, entry_price, confidence, move_pct, volume)
                        SELECT id, timestamp, symbol,
                            COALESCE(direction, ''),
                            COALESCE(price, 0.0),
                            COALESCE(confidence, 0.0),
                            COALESCE(move_pct, 0.0),
                            volume
                        FROM signals;
                    DROP TABLE IF EXISTS signals;
                    ALTER TABLE signals_v3 RENAME TO signals;
                    CREATE INDEX IF NOT EXISTS idx_signals_ts ON signals(timestamp);
                """)
                count = conn.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
                logger.info("Full migration complete — %d old signals preserved", count)
        else:
            # Fresh table — create new schema directly
            conn.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    direction TEXT DEFAULT '',
                    entry_price REAL DEFAULT 0.0,
                    take_profit REAL DEFAULT 0.0,
                    stop_loss REAL DEFAULT 0.0,
                    confidence REAL DEFAULT 0.0,
                    move_pct REAL DEFAULT 0.0,
                    volume REAL,
                    atr_pct REAL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_signals_ts ON signals(timestamp)
            """)
    except Exception as e:
        logger.error("init_db failed: %s — wiping orphan tables and retrying", e)
        conn.executescript("""
            DROP TABLE IF EXISTS signals_v2;
            DROP TABLE IF EXISTS signals_v3;
        """)
        conn.commit()
    finally:
        conn.close()


def write_signal(signal: Signal) -> None:
    """Write a signal to SQLite."""
    conn = sqlite3.connect(str(SIGNALS_DB))
    try:
        conn.execute(
            "INSERT INTO signals (timestamp, symbol, direction, entry_price, take_profit, stop_loss, confidence, move_pct, volume, atr_pct) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            signal.to_db_tuple(),
        )
        conn.commit()
    except Exception as e:
        logger.error("write_signal failed: %s", e)
    finally:
        conn.close()


def signal_count() -> int:
    """Return total signals in DB."""
    conn = sqlite3.connect(str(SIGNALS_DB))
    try:
        return conn.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
    finally:
        conn.close()


def write_health(state: dict) -> None:
    """Atomically write health JSON file."""
    tmp = HEALTH_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, default=str))
    tmp.rename(HEALTH_FILE)


# ── Price Tracker ───────────────────────────────────────────────────────────

@dataclass(slots=True)
class PriceTracker:
    """
    Maintains a sliding window of price data per symbol.
    
    Tracks high/low within each window for ATR-based TP/SL calculation.
    Emits a Signal when price moves beyond PRICE_MOVE_THRESHOLD from the
    window anchor price.
    """
    WINDOW_SECONDS: int = 60         # 1-minute windows for volatility
    MIN_WINDOW_TICKS: int = 5         # minimum ticks before evaluating signals (for 0.08% threshold)
    _prices: dict = field(default_factory=dict)
    _window_anchor: dict = field(default_factory=dict)
    _tick_counts: dict[str, int] = field(default_factory=dict)
    _window_highs: dict[str, float] = field(default_factory=dict)
    _window_lows: dict[str, float] = field(default_factory=dict)

    def seed(self, symbol: str, price: float, volume: Optional[float] = None) -> None:
        """Seed initial price and start the first window."""
        now = time.time()
        self._prices[symbol] = {"price": price, "volume": volume}
        self._window_anchor[symbol] = {"price": price, "epoch_start": now, "volume": volume}
        self._window_highs[symbol] = price
        self._window_lows[symbol] = price
        self._tick_counts[symbol] = 0

    def _reset_window(self, symbol: str, now: float, price: float, volume: Optional[float] = None) -> None:
        """Start a fresh window with the given price as anchor."""
        self._window_anchor[symbol] = {"price": price, "epoch_start": now, "volume": volume}
        self._window_highs[symbol] = price
        self._window_lows[symbol] = price
        self._tick_counts[symbol] = 0

    def _compute_tp_sl(self, symbol: str, entry: float, direction: str) -> tuple[float, float]:
        """
        Compute take-profit and stop-loss levels based on ATR (high-low range)
        within the current detection window.
        
        ATR = (high - low) / entry * 100 (as percentage of entry price)
        TP multiplier: 2x ATR (capped at 5%)
        SL multiplier: 0.5x ATR (floored at 0.3%)
        """
        high = self._window_highs.get(symbol, entry)
        low = self._window_lows.get(symbol, entry * 0.995)
        atr_pct = max((high - low) / entry * 100, 0.1)
        
        if direction == "long":
            tp_mult = min(atr_pct * 2.0, 5.0) / 100.0
            sl_mult = max(atr_pct * 0.5, 0.3) / 100.0
            tp = round(entry * (1 + tp_mult), 2)
            sl = round(entry * (1 - sl_mult), 2)
        else:
            tp_mult = min(atr_pct * 2.0, 5.0) / 100.0
            sl_mult = max(atr_pct * 0.5, 0.3) / 100.0
            tp = round(entry * (1 - tp_mult), 2)
            sl = round(entry * (1 + sl_mult), 2)
        
        return tp, sl, round(atr_pct, 4)

    def update(self, symbol: str, price: float, volume: Optional[float] = None) -> Optional[Signal]:
        """Ingest a new tick. Returns a Signal with entry, TP, SL if move exceeds threshold."""
        now = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()
        prev = self._prices.get(symbol)

        if prev is None:
            self.seed(symbol, price, volume)
            return None

        self._prices[symbol] = {"price": price, "volume": volume or prev.get("volume")}

        anchor = self._window_anchor.get(symbol)
        if anchor is None or (now - anchor["epoch_start"]) >= self.WINDOW_SECONDS:
            self._reset_window(symbol, now, price, volume)
            return None

        if price > self._window_highs.get(symbol, price):
            self._window_highs[symbol] = price
        if price < self._window_lows.get(symbol, price):
            self._window_lows[symbol] = price

        self._tick_counts[symbol] = self._tick_counts.get(symbol, 0) + 1

        if self._tick_counts[symbol] < self.MIN_WINDOW_TICKS:
            return None

        anchor_price = anchor["price"]
        if anchor_price == 0:
            return None

        move_pct = ((price - anchor_price) / anchor_price) * 100.0

        if abs(move_pct) >= PRICE_MOVE_THRESHOLD:
            direction = "long" if move_pct > 0 else "short"
            confidence = min(abs(move_pct) / 5.0, 1.0)
            tp, sl, atr_pct = self._compute_tp_sl(symbol, anchor_price, direction)

            logger.info(
                "SIGNAL: %s %s entry=%.2f TP=%.2f SL=%.2f (%.4f%% move, ATR=%.2f%%)",
                symbol, direction.upper(), price, tp, sl,
                move_pct, atr_pct
            )
            sig = Signal(
                timestamp=now_iso,
                symbol=symbol,
                direction=direction,
                entry_price=price,
                take_profit=tp,
                stop_loss=sl,
                confidence=round(confidence, 4),
                move_pct=round(move_pct, 4),
                volume=volume or anchor.get("volume"),
                atr_pct=atr_pct,
            )
            return sig

        return None


# ── WebSocket Client ────────────────────────────────────────────────────────

class CoinbaseClient:
    """WebSocket client for Coinbase Advanced Trade ticker feed."""
    
    SUBSCRIBE_TEMPLATE = {
        "type": "subscribe",
        "product_ids": SCAN_SYMBOLS,
        "channel": "ticker",
    }

    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        self.tracker = PriceTracker()
        self._stop = False
        self._ws = None
        self._signals_this_session = 0

    def stop(self) -> None:
        self._stop = True

    async def connect(self) -> None:
        retry = 1
        write_health({"status": "starting", "connected_since": None, "signals_this_session": 0, "total_signals": signal_count()})
        while not self._stop:
            try:
                logger.info("connecting to %s", COINBASE_WS_URL)
                async with websockets.connect(COINBASE_WS_URL) as ws:
                    self._ws = ws
                    write_health({"status": "connected", "connected_since": datetime.now(timezone.utc).isoformat(),
                                  "signals_this_session": self._signals_this_session, "total_signals": signal_count()})
                    await ws.send(json.dumps(self.SUBSCRIBE_TEMPLATE))
                    msg = await ws.recv()
                    data = json.loads(msg)
                    logger.info("subscription confirmed: %s", json.dumps(data.get("result", data)))
                    retry = 1

                    async for raw in ws:
                        if self._stop:
                            break
                        try:
                            tick = json.loads(raw)
                        except json.JSONDecodeError:
                            continue
                        channel = tick.get("channel", "")
                        if channel != "ticker":
                            continue
                        events = tick.get("events", [])
                        for ev in events:
                            tickers = ev.get("tickers", [])
                            for t in tickers:
                                symbol = t.get("product_id", "")
                                price_s = t.get("price", "")
                                volume_s = t.get("volume_24_h", "")
                                if not symbol or not price_s:
                                    continue
                                try:
                                    price = float(price_s)
                                except (ValueError, TypeError):
                                    continue
                                volume = float(volume_s) if volume_s else None
                                signal = self.tracker.update(symbol, price, volume)
                                if signal is not None:
                                    self._signals_this_session += 1
                                    write_signal(signal)
                                    logger.info(
                                        "SIGNAL: %s %s entry=%.2f TP=%.2f SL=%.2f (%.2f%% move)",
                                        signal.symbol, signal.direction.upper(),
                                        signal.entry_price, signal.take_profit,
                                        signal.stop_loss, signal.move_pct
                                    )
                                    print(signal.to_json(), flush=True)
                                    await self.queue.put(signal)
            except (websockets.ConnectionClosed, OSError, asyncio.TimeoutError) as exc:
                if not self._stop:
                    logger.warning("connection lost (%s), reconnecting in %ds", exc, retry)
                    write_health({"status": f"reconnecting in {retry}s", "error": str(exc),
                                  "signals_this_session": self._signals_this_session, "total_signals": signal_count()})
                    await asyncio.sleep(retry)
                    retry = min(retry * 2, 60)
            except Exception as exc:
                logger.error("unexpected error: %s", exc, exc_info=True)
                if not self._stop:
                    await asyncio.sleep(retry)
                    retry = min(retry * 2, 60)

    @property
    def signals_this_session(self) -> int:
        return self._signals_this_session


# ── Queue & Signal Processor ────────────────────────────────────────────────

class SignalProcessor:
    """Processes signals from the queue for external routing or logging."""

    def __init__(self, queue: asyncio.Queue):
        self.queue = queue

    async def run(self) -> None:
        while True:
            signal = await self.queue.get()
            try:
                pass  # Future: route to execution layer, Telegram, webhook
            except Exception as exc:
                logger.error("signal_processor: %s", exc)


# ── Main ────────────────────────────────────────────────────────────────────

async def main() -> None:
    q: asyncio.Queue[Signal] = asyncio.Queue(maxsize=QUEUE_MAX_SIZE)

    init_db()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger.info(
        "Kestrel Striker starting — symbols=%s, threshold=%.1f%%",
        SCAN_SYMBOLS, PRICE_MOVE_THRESHOLD,
    )

    client = CoinbaseClient(q)

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