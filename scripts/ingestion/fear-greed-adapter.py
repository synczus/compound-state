#!/usr/bin/env python3
"""Fear & Greed Index Adapter — polls alternative.me API, normalizes to signal contract, writes JSONL.

Usage:
  python3 fear-greed-adapter.py
"""

import json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

BASE = Path("/home/synczus/kestrel")
OUT_DIR = BASE / "pulse"
API_URL = "https://api.alternative.me/fng/?limit=2"
SOURCE_NAME = "fear-greed"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"


def fetch_fng():
    """Fetch Fear & Greed Index data from alternative.me API."""
    try:
        req = Request(API_URL, headers={"User-Agent": USER_AGENT})
        data = urlopen(req, timeout=15).read()
        return json.loads(data)
    except Exception as e:
        print(f"[{SOURCE_NAME}] API fetch failed: {e}", file=sys.stderr)
        return None


def parse_timestamp(timestamp_str: str | int) -> int:
    """Parse timestamp into nanosecond epoch."""
    try:
        return int(int(timestamp_str) * 1_000_000_000)
    except (ValueError, TypeError):
        return int(time.time() * 1_000_000_000)


def normalize(api_data: dict) -> list[dict]:
    """Convert API response to signal contract events."""
    events = []
    if not api_data or "data" not in api_data:
        print(f"[{SOURCE_NAME}] No data in API response", file=sys.stderr)
        return events

    items = api_data["data"]
    if not items:
        return events

    current = items[0]
    value = int(current.get("value", 50))
    classification = current.get("value_classification", "Neutral")
    ts_raw = current.get("timestamp")
    ts_ns = parse_timestamp(ts_raw) if ts_raw else int(time.time() * 1_000_000_000)

    # Previous value for comparison
    previous_value = None
    if len(items) > 1:
        previous_value = int(items[1].get("value", 50))

    # Calculate confidence and magnitude
    confidence = round(value / 100.0, 2)
    magnitude = round(abs(value - 50) / 50.0, 2)
    # Determine direction
    direction = "rising" if previous_value is not None and value > previous_value else \
                ("falling" if previous_value is not None and value < previous_value else "steady")

    headline = f"Fear & Greed: {classification}"
    body_parts = {
        "index": value,
        "classification": classification,
    }
    if previous_value is not None:
        body_parts["previous"] = previous_value
    body = json.dumps(body_parts)

    raw_id = f"fear-greed:{ts_raw or int(time.time())}"

    # Metadata from API response
    metadata = api_data.get("metadata", {})
    error = metadata.get("error", None)

    event = {
        "source_id": SOURCE_NAME,
        "event_type": "sentiment",
        "timestamp": ts_ns,
        "payload": {
            "headline": headline,
            "body": body,
            "symbols": ["BTC", "ETH"],
            "metrics": {
                "confidence": confidence,
                "magnitude": magnitude,
                "velocity": direction,
            }
        },
        "provenance": {
            "source_url": "https://alternative.me/crypto/fear-and-greed-index/",
            "raw_message_id": raw_id,
            "verified": False,
            "verified_by": f"adapter-{SOURCE_NAME}",
        }
    }

    events.append(event)
    return events


def write_output(events: list[dict]):
    """Write events to per-source JSONL file."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{SOURCE_NAME}-inbox.jsonl"
    with open(out_path, "w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")
    return out_path


def main():
    print(f"[{SOURCE_NAME}] Fetching Fear & Greed Index...", file=sys.stderr)
    api_data = fetch_fng()

    if not api_data:
        print(f"[{SOURCE_NAME}] Failed to fetch data", file=sys.stderr)
        return 1

    events = normalize(api_data)
    if not events:
        print(f"[{SOURCE_NAME}] No events generated", file=sys.stderr)
        return 1

    out_path = write_output(events)
    print(f"[{SOURCE_NAME}] {len(events)} events → {out_path}", file=sys.stderr)

    # Stats output
    for e in events:
        m = e["payload"]["metrics"]
        print(f"\n📡 {SOURCE_NAME} adapter:", file=sys.stderr)
        print(f"   Value: {json.loads(e['payload']['body']).get('index', '?')}", file=sys.stderr)
        print(f"   Classification: {e['payload']['headline'].split(':')[-1].strip()}", file=sys.stderr)
        print(f"   Confidence: {m['confidence']}", file=sys.stderr)
        print(f"   Magnitude: {m['magnitude']}", file=sys.stderr)
        print(f"   Velocity: {m['velocity']}", file=sys.stderr)
        print(f"   Symbols: {e['payload']['symbols']}", file=sys.stderr)
        print(f"   Output: {out_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())