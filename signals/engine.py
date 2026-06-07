"""
SignalRouter — pops Tick objects from the queue and evaluates signal logic.
First version: simple price-move threshold against the 24h open.
Replace / extend evaluate() with RSI/Bollinger/volume logic later.

Hardening (v2):
  - Alert deduplication: same symbol not re-alerted within _ALERT_COOLDOWN
    unless move has shifted by >= _ALERT_MOVE_DELTA percentage points.
  - Persistent state: dedup table written to JSON so alerts survive restarts.
  - Health pulse: logs ticks_processed + queue_depth every 60s so journalctl
    shows the service is alive even during quiet market periods.
"""
import asyncio
import json
import logging
import os
import time
from pathlib import Path

from core.config import PRICE_MOVE_THRESHOLD, KESTREL_ROOT
from scanner.normalizer import Tick
from signals.telegram import format_signal, send_alert

logger = logging.getLogger("kestrel.engine")

_ALERT_COOLDOWN = 300    # seconds: minimum gap between alerts for the same symbol
_ALERT_MOVE_DELTA = 0.2  # re-alert before cooldown if move shifts by this many % points
_HEALTH_INTERVAL = 60    # seconds between health pulse log lines
_DEDUP_FILE = KESTREL_ROOT / "signals" / ".last_alert.json"


def _load_dedup() -> dict[str, tuple[float, float]]:
    """Load persistent alert dedup state from disk."""
    try:
        raw = json.loads(Path(_DEDUP_FILE).read_text())
        return {k: (v[0], v[1]) for k, v in raw.items()}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _save_dedup(state: dict[str, tuple[float, float]]) -> None:
    """Persist dedup state to disk atomically."""
    try:
        Path(_DEDUP_FILE).parent.mkdir(parents=True, exist_ok=True)
        tmp = f"{_DEDUP_FILE}.tmp"
        Path(tmp).write_text(
            json.dumps({k: list(v) for k, v in state.items()}, indent=2)
        )
        os.replace(tmp, _DEDUP_FILE)
    except OSError:
        pass


class SignalRouter:
    def __init__(self, queue: asyncio.Queue):
        self.queue: asyncio.Queue = queue
        self._running = True
        self._ticks_processed: int = 0
        self._last_health: float = 0.0
        # symbol -> (last_move_pct, alert_time_monotonic) — loaded from disk
        self._last_alert: dict[str, tuple[float, float]] = _load_dedup()
        if self._last_alert:
            logger.info(
                "Loaded %d persistent alert records from %s",
                len(self._last_alert), _DEDUP_FILE,
            )

    def stop(self) -> None:
        self._running = False

    async def process_loop(self) -> None:
        """
        Continuous consumer. Pops ticks, runs evaluate(), dispatches alerts.
        Emits a health pulse to stdout/journald every _HEALTH_INTERVAL seconds.
        """
        logger.info("SignalRouter online | threshold=%.2f%%", PRICE_MOVE_THRESHOLD)
        self._last_health = time.monotonic()

        while self._running:
            # Health pulse — proves liveness in journalctl during quiet periods
            now = time.monotonic()
            if now - self._last_health >= _HEALTH_INTERVAL:
                logger.info(
                    "Health | ticks_processed=%d | queue_depth=%d",
                    self._ticks_processed,
                    self.queue.qsize(),
                )
                self._last_health = now

            try:
                tick: Tick = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            self._ticks_processed += 1
            try:
                await self.evaluate(tick)
            except Exception as e:
                logger.error("evaluate() crashed for %s: %s", tick.symbol, e)
            finally:
                self.queue.task_done()

        logger.info("SignalRouter stopped.")

    def _should_alert(self, symbol: str, move_pct: float) -> bool:
        """
        Deduplication gate with persistent state.
        Returns True if an alert should fire.
        Suppresses re-alerts within _ALERT_COOLDOWN unless the move has
        shifted by >= _ALERT_MOVE_DELTA percentage points.
        """
        if symbol not in self._last_alert:
            return True
        last_move, last_time = self._last_alert[symbol]
        if time.monotonic() - last_time >= _ALERT_COOLDOWN:
            return True
        if abs(move_pct - last_move) >= _ALERT_MOVE_DELTA:
            return True
        return False

    async def evaluate(self, tick: Tick) -> None:
        """
        Signal evaluation. Currently: price move vs 24h open.
        Extend here with RSI, Bollinger, volume confluence, etc.
        """
        if tick.open <= 0:
            return

        move_pct = ((tick.price - tick.open) / tick.open) * 100
        abs_move = abs(move_pct)

        logger.debug(
            "%s  price=%.4f  open=%.4f  move=%+.2f%%",
            tick.symbol, tick.price, tick.open, move_pct,
        )

        if abs_move < PRICE_MOVE_THRESHOLD:
            return

        if not self._should_alert(tick.symbol, move_pct):
            logger.debug("DEDUP %s | move=%+.2f%% | suppressed", tick.symbol, move_pct)
            return

        direction = "up" if move_pct > 0 else "down"
        msg = format_signal(tick.symbol, tick.price, tick.open, move_pct, direction)
        logger.info("SIGNAL %s | move=%+.2f%% | suppressed (Telegram alerts disabled, use portfolio-snapshot cron)", tick.symbol, move_pct)
        # Telegram alerts are disabled. Market data still flows to portfolio-snapshot cron.
        # await send_alert(msg)
        self._last_alert[tick.symbol] = (move_pct, time.monotonic())
        _save_dedup(self._last_alert)