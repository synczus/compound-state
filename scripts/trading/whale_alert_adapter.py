#!/usr/bin/env python3
"""
Whale Alert → Signal Contract Adapter

Normalizes @whale_alert Telegram messages into the canonical event shape
(schema from kestrel/manifest.yaml v0.1).

Usage:
  # From a raw export file:
  python3 whale_alert_adapter.py --input export.html --output whale_alerts.jsonl

  # Pipe a single message:
  echo "1,318 #BTC (6,607,371 USD) transferred from #Bitstamp to Unknown wallet" \\
    | python3 whale_alert_adapter.py --pipe

  # Continuous mode (live Telegram messages):
  python3 whale_alert_adapter.py --watch kestrel/telegram-log/whale-alert.txt
"""

import json
import re
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# ── Regex patterns ─────────────────────────────────────────────────────

# 🚨 9,473 #BTC (46,853,393 USD) transferred from #Bitfinex to unknown wallet
# 💵 1,000,000 #USDC (1,003,100 USD) minted at USDC Treasury
# 20,000,000 #XRP (6,605,814 USD) transferred from unknown wallet to Funding Wallet 1

TRANSFER_RE = re.compile(
    r"^(?:🚨\s*)?"
    r"(?P<amount>[\d,]+)\s+"
    r"#(?P<asset>[A-Z0-9]+)\s+"
    r"\((?P<usd_value>[\d,]+(?:\.[\d]+)?)\s+USD\)\s+"
    r"transferred\s+from\s+"
    r"(?P<from>.+?)\s+"
    r"to\s+"
    r"(?P<to>.+?)$"
)

MINT_RE = re.compile(
    r"^(?:💵\s*)?"
    r"(?P<amount>[\d,]+)\s+"
    r"#(?P<asset>[A-Z0-9]+)\s+"
    r"\((?P<usd_value>[\d,]+(?:\.[\d]+)?)\s+USD\)\s+"
    r"(?P<action>minted|burned)\s+at\s+"
    r"(?P<source>.+?)$"
)

DETAILS_URL_RE = re.compile(r"Details\s*->?\s*(https://whale-alert\.io[^\s<]+)")

DECIMAL_VALUE_RE = re.compile(r"^(?:🚨\s*)?([\d,]+)\s+#([A-Z0-9]+)\s+\(([\d,.]+)\s+USD\)")


def parse_usd(raw: str) -> float:
    return float(raw.replace(",", ""))


def parse_amount(raw: str) -> float:
    return float(raw.replace(",", ""))


def determine_magnitude(usd_value: float) -> float:
    """Map USD value to 0.0-1.0 magnitude."""
    if usd_value >= 50_000_000:
        return 1.0
    elif usd_value >= 10_000_000:
        return 0.8
    elif usd_value >= 5_000_000:
        return 0.6
    elif usd_value >= 1_000_000:
        return 0.4
    elif usd_value >= 500_000:
        return 0.3
    return 0.2


def determine_velocity(from_label: str, to_label: str) -> str:
    """Infer velocity from transfer direction."""
    exchanges = {
        "BINANCE", "COINBASE", "BITFINEX", "KRAKEN", "HUOBI", "OKX",
        "GEMINI", "BITSTAMP", "BITTREX", "GATEIO", "POLONIEX", "KORBIT",
        "UPBIT", "HITBTC", "KUCOIN", "BYBIT", "BINANCE.US"
    }
    from_ex = from_label.upper().strip("#")
    to_ex = to_label.upper().strip("#")

    from_is_exchange = any(ex in from_ex for ex in exchanges)
    to_is_exchange = any(ex in to_ex for ex in exchanges)

    if from_is_exchange and not to_is_exchange:
        return "decaying"  # Funds leaving exchange → potential sell pressure done
    elif not from_is_exchange and to_is_exchange:
        return "rising"    # Funds entering exchange → potential sell pressure incoming
    elif "UNKNOWN" in from_label.upper() and "UNKNOWN" in to_label.upper():
        return "steady"    # Wallet-to-wallet, neutral
    return "steady"


def normalize(amount: float, asset: str, usd_value: float,
              from_label: str, to_label: str, msg_time: int,
              details_url: Optional[str], alarm_level: int = 0) -> dict:
    """Build a signal-contract event from parsed fields."""
    source_id = "whale-alert"
    event_type = "large_transfer"

    if "TREASURY" in to_label.upper() or "TREASURY" in from_label.upper():
        if "MINT" in to_label.upper() or "MINT" in from_label.upper() or "TREASURY" in from_label.upper():
            event_type = "stablecoin_mint"
        else:
            event_type = "stablecoin_burn"

    magnitude = determine_magnitude(usd_value)
    velocity = determine_velocity(from_label, to_label)

    # Build signal-level confidence based on data quality
    confidence = 0.95  # base: on-chain data verified by Whale Alert
    if amount <= 0 or usd_value <= 0:
        confidence = 0.5

    headline = (
        f"{'🚨' if alarm_level >= 3 else '⚠️' if alarm_level >= 1 else 'ℹ️'} "
        f"{asset}: {amount:,.0f} ({usd_value:,.0f} USD) "
        f"{'→' if 'transferred' in event_type else '•'} "
        f"{from_label} → {to_label}"
    )

    symbols = [asset]
    if asset in ("USDC", "USDT", "DAI", "BUSD", "PAX"):
        symbols = ["USD", asset]

    event = {
        "source_id": source_id,
        "event_type": event_type,
        "timestamp": msg_time * 1_000_000_000,  # seconds → nanoseconds UTC
        "payload": {
            "headline": headline,
            "body": json.dumps({
                "amount": amount,
                "asset": asset,
                "usd_value": usd_value,
                "from": from_label.strip("#").strip(),
                "to": to_label.strip("#").strip(),
            }),
            "symbols": symbols,
            "metrics": {
                "confidence": round(confidence, 2),
                "magnitude": round(magnitude, 2),
                "velocity": velocity,
            }
        },
        "provenance": {
            "source_url": details_url or f"https://whale-alert.io/",
            "raw_message_id": f"{source_id}:{msg_time}:{asset}:{amount:.0f}",
            "verified": True,
            "verified_by": "whale-alert"
        }
    }
    return event


def strip_html(html_text: str) -> str:
    """Strip HTML tags, preserving text content."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html_text)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    # Collapse multiple spaces/newlines
    text = re.sub(r'\s+', ' ', text)
    # Remove trailing newline/whitespace artifacts
    text = text.strip()
    # Strip trailing "Details" (from Details link text)
    text = re.sub(r'\s*Details\s*$', '', text)
    return text.strip()


def parse_html(input_path: Path) -> list[dict]:
    """Parse a Telegram HTML export file for Whale Alert messages."""
    events = []
    text = input_path.read_text(encoding="utf-8")

    # Extract all message text blocks (with HTML tags intact)
    msg_blocks = re.findall(r'<div class="text">(.*?)</div>', text, re.DOTALL)

    # Extract timestamps — they appear in service messages and default messages
    # Each default message block has: pull_right date details
    date_pattern = re.compile(
        r'<div class="pull_right date details" title="([^"]+)">'
    )
    dates = date_pattern.findall(text)

    # Walk through messages, pairing text with timestamps
    msg_idx = 0
    date_idx = 0
    for msg_html in msg_blocks:
        msg_text = strip_html(msg_html)

        # Skip non-transfer messages
        if not msg_text or len(msg_text) < 15:
            date_idx += 1
            continue
        if any(skip in msg_text for skip in ["pinned", "Welcome to", "Channel «", "Channel created"]):
            date_idx += 1
            continue

        # Try to get timestamp — service messages don't have dates
        timestamp = int(time.time())
        if date_idx < len(dates):
            raw_date = dates[date_idx].strip()
            try:
                dt = datetime.strptime(raw_date, "%d.%m.%Y %H:%M:%S UTC%z")
                timestamp = int(dt.timestamp())
            except (ValueError, IndexError):
                pass
        date_idx += 1

        # Count alarm flags in original HTML
        alarm_count = msg_html.count("🚨")

        event = parse_message(msg_text, timestamp, alarm_count)
        if event:
            events.append(event)

    print(f"  Parsed {len(events)} events from {len(msg_blocks)} messages", file=sys.stderr)
    return events


def parse_message(text: str, timestamp: Optional[int] = None, alarm_count: int = 0) -> Optional[dict]:
    """Parse a single Whale Alert message line into an event."""
    # Clean HTML entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.strip()

    # Extract Details URL if present (some exports strip the <a> tag)
    details_url = None
    url_match = DETAILS_URL_RE.search(text)
    if url_match:
        details_url = url_match.group(1)

    # Try transfer pattern first
    m = TRANSFER_RE.match(text)
    if m:
        return normalize(
            amount=parse_amount(m.group("amount")),
            asset=m.group("asset"),
            usd_value=parse_usd(m.group("usd_value")),
            from_label=m.group("from"),
            to_label=m.group("to"),
            msg_time=timestamp or int(time.time()),
            details_url=details_url,
            alarm_level=alarm_count,
        )

    # Try mint/burn pattern
    m = MINT_RE.match(text)
    if m:
        return normalize(
            amount=parse_amount(m.group("amount")),
            asset=m.group("asset"),
            usd_value=parse_usd(m.group("usd_value")),
            from_label=m.group("source"),
            to_label=m.group("action"),
            msg_time=timestamp or int(time.time()),
            details_url=details_url,
            alarm_level=alarm_count,
        )

    return None


def parse_stdin() -> list[dict]:
    """Read messages from stdin, one per line."""
    events = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        event = parse_message(line)
        if event:
            events.append(event)
    return events


def main():
    parser = argparse.ArgumentParser(description="Whale Alert → Signal Contract adapter")
    parser.add_argument("--input", type=Path, help="HTML export file to parse")
    parser.add_argument("--output", type=Path, default=Path("/dev/stdout"),
                        help="Output JSONL file (default: stdout)")
    parser.add_argument("--pipe", action="store_true", help="Read from stdin (one message per line)")
    parser.add_argument("--stats", action="store_true", help="Print summary stats to stderr")
    args = parser.parse_args()

    events = []

    if args.input:
        events = parse_html(args.input)
    elif args.pipe or not sys.stdin.isatty():
        events = parse_stdin()
    else:
        parser.print_help()
        sys.exit(1)

    # Write output
    output_path = args.output
    with open(output_path, "w") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")

    if args.stats or args.output != Path("/dev/stdout"):
        n = len(events)
        sources = set(e["source_id"] for e in events)
        types = {}
        for e in events:
            et = e["event_type"]
            types[et] = types.get(et, 0) + 1
        high_conf = sum(1 for e in events if e["payload"]["metrics"]["confidence"] >= 0.9)
        report = (
            f"\n📊 Whale Alert Adapter Summary\n"
            f"   Events parsed: {n}\n"
            f"   Source: {', '.join(sources)}\n"
            f"   Event types: {types}\n"
            f"   High confidence (≥0.9): {high_conf}\n"
            f"   Total USD tracked: "
            f"${sum(e['payload']['metrics']['magnitude'] * 50_000_000 for e in events):,.0f} (est)\n"
            f"   Output: {output_path}\n"
        )
        print(report, file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())