"""
Centralized config loader — reads from environment (set by .env via systemd EnvironmentFile).
"""
import os
from pathlib import Path

KESTREL_ROOT = Path(__file__).parent.parent

# Telegram
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

# === Exchange Settings ===
EXCHANGE = "coinbase"
# Advanced Trade API (newer) — try this first
# If you get connection errors, switch to: wss://ws-feed.pro.coinbase.com
COINBASE_WS_URL = os.getenv("COINBASE_WS_URL", "wss://advanced-trade-ws.coinbase.com")

# Symbols in Coinbase format (BTC-USD, not btcusdt)
SCAN_SYMBOLS: list[str] = [
    s.strip().upper()
    for s in os.getenv("SCAN_SYMBOLS", "BTC-USD,ETH-USD,SOL-USD").split(",")
    if s.strip()
]

# Signal thresholds
PRICE_MOVE_THRESHOLD: float = float(os.getenv("PRICE_MOVE_THRESHOLD", "0.5"))

# Queue
QUEUE_MAX_SIZE: int = int(os.getenv("QUEUE_MAX_SIZE", "1000"))
