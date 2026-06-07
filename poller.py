import asyncio
import logging
import random
import os
import signal
import sys
from typing import List, Optional
from datetime import datetime, timezone

from scanners.github_hunter import DEFAULT_TARGETS, run_single_hunt, RepoTarget
from scanners.state_manager import StateManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("kestrel.poller")

# GitHub unauthenticated rate limit: 60 req/hour
# 10 repos = 10 req/cycle => max 6 cycles/hour = 1 every 10 min
# Add jitter so we don't hit the ceiling
BASE_INTERVAL = 600  # 10 minutes in seconds
JITTER_MAX = 120     # +/- 2 minutes of jitter
BACKOFF_BASE = 300   # base backoff on rate-limit hit (5 min)
MAX_BACKOFF = 3600   # max backoff (1 hour)

RUNNING = True

def signal_handler(sig, frame):
    global RUNNING
    logger.info("SIGTERM received. Shutting down poller gracefully...")
    RUNNING = False

class BackgroundPoller:
    """
    Sovereign Background Poller.
    Runs a multi-repo commit hunt on a timer, respecting rate limits.
    """
    def __init__(self, targets: Optional[List[RepoTarget]] = None):
        self.targets = targets or DEFAULT_TARGETS
        self.state = StateManager()
        self.backoff = BASE_INTERVAL
        self.consecutive_failures = 0

    def _calculate_interval(self) -> int:
        """Calculate polling interval with jitter and backoff."""
        base = BASE_INTERVAL + self.backoff
        jitter = random.randint(-JITTER_MAX, JITTER_MAX)
        interval = max(60, base + jitter)  # never go below 1 minute
        return interval

    async def poll_cycle(self) -> int:
        """
        Run one full poll cycle across all targets.
        Returns number of new signals found.
        """
        logger.info(f"Starting poll cycle: {len(self.targets)} targets")
        total_signals = 0
        hit_limit = False

        for target in self.targets:
            if not RUNNING:
                break

            try:
                signals = await run_single_hunt(target.owner, target.repo, target.description)
                total_signals += len(signals)

                if signals:
                    logger.info(f"Found {len(signals)} new signals in {target.owner}/{target.repo}")

                self.consecutive_failures = 0
                self.backoff = BASE_INTERVAL

            except Exception as e:
                logger.error(f"Poll failed for {target.owner}/{target.repo}: {e}")
                self.consecutive_failures += 1

                # Check if it's a rate-limit issue
                if "403" in str(e) or "rate limit" in str(e).lower():
                    hit_limit = True
                    self.backoff = min(self.backoff * 2, MAX_BACKOFF)
                    logger.warning(f"Rate limit hit. Backing off to {self.backoff}s")
                    break

            # Stagger requests within the cycle to avoid burst
            await asyncio.sleep(random.uniform(1, 3))

        return total_signals

    async def run_forever(self):
        """Main background loop."""
        logger.info("Kestrel Background Poller starting...")
        logger.info(f"Monitoring {len(self.targets)} repos")

        while RUNNING:
            try:
                interval = self._calculate_interval()
                signals_found = await self.poll_cycle()

                if signals_found > 0:
                    logger.info(f"Cycle complete: {signals_found} new signals sent to hub")
                else:
                    logger.info("Cycle complete: no new signals")

                logger.info(f"Next poll in ~{interval // 60}m (jittered)")
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info("Poller cancelled.")
                break
            except Exception as e:
                logger.error(f"Poller cycle crashed: {e}")
                await asyncio.sleep(60)

        logger.info("Poller stopped.")

async def main():
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    poller = BackgroundPoller()
    await poller.run_forever()

if __name__ == "__main__":
    asyncio.run(main())