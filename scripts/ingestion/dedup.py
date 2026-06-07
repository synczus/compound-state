#!/usr/bin/env python3
"""
Dedup Engine v0.2 — content-hash deduplication for signal events.

Content hash: SHA256(source_id + raw_message_id + headline) truncated to 16 hex chars.
Whale Alert: also extracts tx-hash from payload.body (if present) for tx-level dedup.

Rolling 30-day store at /home/synczus/kestrel/dedup-store.json
Auto-clean entries older than 30 days on every run.

Usage:
  cat events.jsonl | python3 dedup.py --stdin              ← filter duplicates, pass through unique
  cat events.jsonl | python3 dedup.py --stdin --stats      ← same, with verbose stats
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time

KESTREL_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEDUP_STORE = os.path.join(KESTREL_ROOT, "dedup-store.json")
DEDUP_DAYS = 30
DEDUP_SECONDS = DEDUP_DAYS * 86400


def load_store() -> dict:
    """Load the dedup store (hash → timestamp dict)."""
    try:
        with open(DEDUP_STORE) as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        return {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_store(store: dict) -> None:
    """Atomically persist the dedup store."""
    os.makedirs(os.path.dirname(DEDUP_STORE), exist_ok=True)
    tmp = DEDUP_STORE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(store, f)
    os.replace(tmp, DEDUP_STORE)


def content_hash(event: dict) -> str:
    """
    Content hash from (source_id + raw_message_id + headline).
    SHA256 truncated to 16 hex chars.
    """
    source_id = event.get("source_id", "")
    raw_message_id = event.get("provenance", {}).get("raw_message_id", "")
    headline = event.get("payload", {}).get("headline", "")
    raw = f"{source_id}:{raw_message_id}:{headline}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def extract_tx_hash(event: dict) -> str | None:
    """
    For Whale Alert specifically: extract tx-hash from payload.body.
    The body field is a JSON string; look for "tx_hash", "transaction_id",
    or "hash" keys at the top level or inside a "transaction" sub-object.
    """
    body_raw = event.get("payload", {}).get("body", "")
    if not body_raw or not isinstance(body_raw, str):
        return None
    try:
        body = json.loads(body_raw)
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(body, dict):
        return None

    # Direct keys
    for key in ("tx_hash", "transaction_id", "hash", "txid"):
        val = body.get(key)
        if val and isinstance(val, str) and len(val) > 10:
            return val

    # Nested in "transaction"
    tx = body.get("transaction", {})
    if isinstance(tx, dict):
        for key in ("hash", "tx_hash", "transaction_id", "txid"):
            val = tx.get(key)
            if val and isinstance(val, str) and len(val) > 10:
                return val

    return None


def extract_tx_hash_from_body(body_raw: str) -> str | None:
    """Regex-based backup: find 64-char hex strings in the body text."""
    if not body_raw:
        return None
    # Common tx hash pattern: 64 hex chars
    matches = re.findall(r'[0-9a-fA-F]{64}', body_raw)
    if matches:
        return matches[0]
    # JSON string patterns: "tx_hash":"xxx" or "transaction_id":"xxx"
    m = re.search(r'"(?:tx_hash|transaction_id|txid|hash)"\s*:\s*"([^"]{20,})"', body_raw)
    if m:
        return m.group(1)
    return None


def cleanup_store(store: dict, now: float) -> int:
    """Remove entries older than DEDUP_SECONDS. Returns count pruned."""
    cutoff = now - DEDUP_SECONDS
    before = len(store)
    store = {k: v for k, v in store.items() if v > cutoff}
    return before - len(store)


def process_events(lines, stats: bool = False) -> tuple[list[dict], dict]:
    """
    Process JSONL lines through dedup filter.
    Returns (unique_events, stats_dict).
    """
    store = load_store()
    now = time.time()

    # Auto-clean old entries
    pruned = cleanup_store(store, now)
    save_store(store)  # persist cleanup immediately

    total_in = 0
    dup_count = 0
    unique_out = 0
    hash_collisions = 0
    tx_collisions = 0
    tx_hashes_seen: set[str] = set()

    results = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        total_in += 1

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Primary: content hash from (source_id + raw_message_id + headline)
        ch = content_hash(event)
        if ch in store:
            dup_count += 1
            hash_collisions += 1
            continue

        # Secondary: for Whale Alert, also check tx-hash
        if event.get("source_id") == "whale-alert":
            tx_hash = extract_tx_hash(event) or extract_tx_hash_from_body(
                event.get("payload", {}).get("body", "")
            )
            if tx_hash:
                tx_key = f"tx:{tx_hash}"
                if tx_key in store:
                    dup_count += 1
                    tx_collisions += 1
                    continue
                tx_hashes_seen.add(tx_key)

        # New unique event — add to store and output
        store[ch] = now
        if tx_hashes_seen:
            for th in tx_hashes_seen:
                store[th] = now
            tx_hashes_seen.clear()

        results.append(event)
        unique_out += 1

    # Persist updated store
    save_store(store)

    if stats:
        stats_dict = {
            "total_in": total_in,
            "duplicates_removed": dup_count,
            "unique_out": unique_out,
            "store_entries": len(store),
            "store_entries_pruned": pruned,
            "hash_collisions": hash_collisions,
            "tx_collisions": tx_collisions,
        }
    else:
        stats_dict = {}

    return results, stats_dict


def main():
    parser = argparse.ArgumentParser(description="Signal Dedup Engine")
    parser.add_argument("--stdin", action="store_true", help="Read JSONL from stdin")
    parser.add_argument("--stats", action="store_true", help="Show stats (even when 0 duplicates)")
    args = parser.parse_args()

    if args.stdin:
        lines = sys.stdin.readlines()
        results, stats = process_events(lines, stats=args.stats or len(lines) > 0)

        for event in results:
            print(json.dumps(event))

        if args.stats and stats:
            print(f"[dedup] in={stats['total_in']} dup={stats['duplicates_removed']} out={stats['unique_out']}"
                  f" store={stats['store_entries']} pruned={stats['store_entries_pruned']}"
                  f" hash_collisions={stats['hash_collisions']} tx_collisions={stats['tx_collisions']}",
                  file=sys.stderr)
        elif not results and not args.stats:
            pass  # silent when no duplicates
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()