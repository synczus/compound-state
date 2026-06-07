#!/usr/bin/env python3
"""DefiLlama TVL Adapter — polls api.llama.fi, extracts top movers, normalizes to signal contract.

Usage:
  python3 defillama-adapter.py
"""

import json, os, sys, time
from pathlib import Path
from urllib.request import Request, urlopen

BASE = Path("/home/synczus/kestrel")
OUT_DIR = BASE / "pulse"
API_URL = "https://api.llama.fi/protocols"
SOURCE_NAME = "defillama"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"

# Max protocols to sort by TVL change
TOP_N = 10
# Max signals to emit per run
EMIT_N = 5


def fetch_protocols():
    """Fetch all protocols from DefiLlama API."""
    try:
        req = Request(API_URL, headers={"User-Agent": USER_AGENT})
        data = urlopen(req, timeout=30).read()
        return json.loads(data)
    except Exception as e:
        print(f"[{SOURCE_NAME}] API fetch failed: {e}", file=sys.stderr)
        return None


def safe_float(val) -> float:
    """Safely convert to float, defaulting to 0.0."""
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def get_symbol(token_symbol: str, protocol_name: str) -> str:
    """Derive a symbol token from the protocol."""
    if not token_symbol:
        return protocol_name.upper()
    s = token_symbol.strip().upper()
    if s.endswith(".E"):
        s = s[:-2]
    if s.endswith("]"):
        s = s.split("[")[0].strip()
    return s


def normalize(top_protocols: list[dict]) -> list[dict]:
    """Convert top protocol data to signal contract events, one per protocol."""
    events = []
    now_ns = int(time.time() * 1_000_000_000)

    for proto in top_protocols:
        name = proto.get("name", "unknown")
        symbol_raw = proto.get("symbol", "")
        symbol = get_symbol(symbol_raw, name)
        tvl = safe_float(proto.get("tvl"))
        change_1d = safe_float(proto.get("change_1d"))

        # Build headline and body
        direction = "up" if change_1d >= 0 else "down"
        headline = f"[TVL {direction.upper()}] {name} TVL {direction} {abs(change_1d):.2f}% in 24h"

        body_parts = {
            "protocol": name,
            "symbol": symbol,
            "tvl": round(tvl, 2) if tvl else None,
            "change_1d_pct": round(change_1d, 2),
            "direction": direction,
        }
        body = json.dumps(body_parts)

        # Compute confidence and magnitude from the baseline
        magnitude = round(min(abs(change_1d) / 50.0, 1.0), 2)

        raw_id = f"defillama:{name}:{int(time.time())}"

        event = {
            "source_id": SOURCE_NAME,
            "event_type": "defi_tvl_flow",
            "timestamp": now_ns,
            "payload": {
                "headline": headline,
                "body": body,
                "symbols": [symbol],
                "metrics": {
                    "confidence": 0.55,  # baseline — will be overridden by coordination.yaml baseline
                    "magnitude": magnitude,
                    "velocity": "rising" if direction == "up" else "falling",
                }
            },
            "provenance": {
                "source_url": f"https://defillama.com/protocol/{name.lower().replace(' ', '-')}",
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
    print(f"[{SOURCE_NAME}] Fetching protocols from DefiLlama...", file=sys.stderr)
    data = fetch_protocols()

    if not data or not isinstance(data, list):
        print(f"[{SOURCE_NAME}] Failed to fetch or unexpected response format", file=sys.stderr)
        return 1

    print(f"[{SOURCE_NAME}] {len(data)} total protocols fetched", file=sys.stderr)

    # Sort by absolute 1d change % to find biggest movers
    def change_abs(p):
        return abs(safe_float(p.get("change_1d", 0)))

    sorted_protos = sorted(data, key=change_abs, reverse=True)
    top_10 = sorted_protos[:TOP_N]

    print(f"[{SOURCE_NAME}] Top {TOP_N} movers by 24h change:", file=sys.stderr)
    for i, p in enumerate(top_10):
        name = p.get("name", "?")
        change = safe_float(p.get("change_1d", 0))
        tvl = safe_float(p.get("tvl", 0))
        print(f"   {i+1}. {name:30s} TVL: {tvl:>12,.0f}  Change: {change:>+8.2f}%", file=sys.stderr)

    # Emit top EMIT_N signals
    emit_protos = top_10[:EMIT_N]
    events = normalize(emit_protos)

    if not events:
        print(f"[{SOURCE_NAME}] No events generated", file=sys.stderr)
        return 1

    out_path = write_output(events)
    print(f"[{SOURCE_NAME}] {len(events)} events → {out_path}", file=sys.stderr)

    # Stats
    print(f"\n📡 {SOURCE_NAME} adapter:", file=sys.stderr)
    for e in events:
        b = json.loads(e["payload"]["body"])
        print(f"   {b['protocol']:30s} {b['change_1d_pct']:>+8.2f}%  TVL: {b['tvl']:>12,.0f}", file=sys.stderr)
    symbols = set()
    for e in events:
        symbols.update(e["payload"]["symbols"])
    print(f"   Symbols: {sorted(symbols)}", file=sys.stderr)
    print(f"   Output: {out_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())