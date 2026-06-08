"""
MarketScanner — REST polling version (Coinbase public endpoints).
More reliable on networks that block/reject WebSocket streams.
Pushes normalized Tick objects to the queue.
"""
import asyncio
import logging
import time
from datetime import datetime, timezone

import httpx

from core.config import SCAN_SYMBOLS, QUEUE_MAX_SIZE
from scanner.normalizer import Tick

logger = logging.getLogger("kestrel.scanner")

_POLL_INTERVAL = 4.0    # seconds between full poll cycles
_HTTP_TIMEOUT = 8.0
_STATS_BASE = "https://api.exchange.coinbase.com/products"


class MarketScanner:
    def __init__(self, queue: asyncio.Queue):
        self.queue: asyncio.Queue = queue
        self._running = True
        self._last_msg_time: float = time.monotonic()

    def stop(self) -> None:
        self._running = False

    async def listen(self) -> None:
        logger.info(
            "MarketScanner starting | mode=rest-poll | symbols=%s | interval=%.1fs",
            SCAN_SYMBOLS, _POLL_INTERVAL,
        )
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            while self._running:
                for symbol in SCAN_SYMBOLS:
                    if not self._running:
                        break
                    tick = await self._fetch_tick(client, symbol)
                    if tick:
                        self._last_msg_time = time.monotonic()
                        self._enqueue(tick)

                await asyncio.sleep(_POLL_INTERVAL)

        logger.info("MarketScanner stopped.")

    async def _fetch_tick(self, client: httpx.AsyncClient, product_id: str) -> Tick | None:
        """
        GET /products/{id}/stats — returns open, high, low, volume, last for the past 24h.
        This is the same endpoint Coinbase Pro UI uses; no auth required.
        """
        try:
            resp = await client.get(f"{_STATS_BASE}/{product_id}/stats")
            if resp.status_code != 200:
                logger.debug(
                    "stats HTTP %s for %s", resp.status_code, product_id
                )
                return None
            d = resp.json()
            price = float(d["last"])
            return Tick(
                symbol=product_id.replace("-", ""),
                price=price,
                open=float(d.get("open", price)),
                high=float(d.get("high", price)),
                low=float(d.get("low", price)),
                volume=float(d.get("volume", 0)),
                timestamp=datetime.now(timezone.utc),
                source="coinbase-rest",
            )
        except Exception as e:
            logger.debug("Fetch failed for %s: %s", product_id, e)
            return None

    def _enqueue(self, tick: Tick) -> None:
        try:
            self.queue.put_nowait(tick)
        except asyncio.QueueFull:
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            self.queue.put_nowait(tick)
            logger.warning("Queue full — dropped oldest tick.")
