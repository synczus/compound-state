#!/usr/bin/env python3
"""
Archive Batch Processor v0.2 — ingests Telegram channel export HTML files
from media/inbound/ and normalizes them into the signal pipeline.

Processes 15+ HTML files (Telegram channel exports) sitting in
~/.openclaw/media/inbound/ and normalizes each message to the signal contract.

DuckDB schema:
  - archive_batches: tracks processed files by content hash
  - archive_messages: normalized signal events

Dedup: SHA256 of (source_id + raw_message_id + body[:200]) stored in
        archive_dedup_store.json (never expires, since these are historical).

Usage:
  python3 archive_ingest.py                         # Process all unprocessed files
  python3 archive_ingest.py --file FILENAME          # Process one file
  python3 archive_ingest.py --force                  # Reprocess even already-processed
  python3 archive_ingest.py --dry-run                # Count messages without inserting
  python3 archive_ingest.py --list                   # List files and their status
  python3 archive_ingest.py --summarize              # Show stats from archive_messages
"""

import argparse
import hashlib
import html as ht
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────

KESTREL_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(KESTREL_ROOT, "signals.duckdb")
INBOUND_DIR = os.path.expanduser("~/.openclaw/media/inbound")
ARCHIVE_DEDUP_PATH = os.path.join(KESTREL_ROOT, "archive_dedup_store.json")

# ── Channel baseline confidence (from spec + common sense defaults) ──────

CHANNEL_BASELINES = {
    "binance-killers": 0.30,
    "glassnode": 0.80,
    "cryptoquant": 0.85,
    "wu-blockchain": 0.40,
    "unfolded": 0.25,
    "diamondcrab-crypto": 0.20,
    "crypto-goodreads": 0.50,
    "the-babylonian": 0.45,
    "qcp-capital": 0.55,
    "messari-tg": 0.60,
    "the-block": 0.55,
    "crypto-garden": 0.20,
    "whale-alert": 0.75,
    "disclosetv": 0.35,
    "gemhunter": 0.15,
    "ai-hangout": 0.40,
    "tyler-trades": 0.15,
}

DEFAULT_BASELINE = 0.20

# ── Source detection by channel title ─────────────────────────────────────

CHANNEL_SOURCE_MAP = {
    "binance killers": "binance-killers",
    "glassnode": "glassnode",
    "cryptoquant": "cryptoquant",
    "wu blockchain": "wu-blockchain",
    "unfolded": "unfolded",
    "diamondcrab": "diamondcrab-crypto",
    "crypto goodreads": "crypto-goodreads",
    "the babylonian": "the-babylonian",
    "qcp capital": "qcp-capital",
    "messari": "messari-tg",
    "the block": "the-block",
    "crypto garden": "crypto-garden",
    "whale alert": "whale-alert",
    "disclose": "disclosetv",
    "gemhunter": "gemhunter",
    "ai hangout": "ai-hangout",
    "tyler trades": "tyler-trades",
}

# ── Crypto symbol regex (comprehensive) ──────────────────────────────────

CRYPTO_SYMBOL_RE = re.compile(
    r"\b("
    r"BTC|XBT|ETH|SOL|XRP|ADA|DOT|AVAX|LINK|MATIC|UNI|ATOM|LTC|BCH|"
    r"XLM|DOGE|SHIB|FTM|NEAR|ALGO|AAVE|APE|FIL|ICP|EOS|XTZ|TRX|VET|"
    r"SAND|MANA|GALA|AXS|CRV|SUSHI|COMP|MKR|YFI|SNX|BNB|USDT|USDC|"
    r"DAI|TUSD|WIF|PEPE|FLOKI|BONK|ENS|RUNE|THETA|FET|AGIX|INJ|KAS|"
    r"SEI|OP|ARB|SUI|TIA|PYTH|JUP|RAY|STX|ORDI|SATS|PENDLE|SSV|LDO|"
    r"RPL|FXS|GMX|GNS|RDNT|ARPA|LPT|HNT|IOTX|CFX|ACH|STG|SLP|PEOPLE|"
    r"MASK|DYDX|SNT|BAT|ZIL|ZEC|DASH|KSM|WAVES|ONT|IOST|NEO|QTUM|ETC|"
    r"SC|CKB|GLMR|MOVR|ROSE|OCEAN|NMR|GTC|AMP|POLY|UMA|BNT|BAL|KAVA|"
    r"AKT|CRO|FTT|SRM|REN|RSR|CVC|GRT|STORJ|LRC|ZRX|ENJ|CHZ|WIN|HOT|"
    r"CELO|XDC|ETHFI|ENA|ZRO|ZK|TAIKO|BLAST|STRK|AR|PIXEL|PORTAL|"
    r"BEAM|AXL|ALT|MANTA|METIS|PHB|NADA|WLD|SAGA|OMNI|REZ|NOT|1000"
    r")\b",
    re.IGNORECASE
)

# ── Timestamp parsing ────────────────────────────────────────────────────

TIMESTAMP_FORMATS = [
    "%d.%m.%Y %H:%M:%S UTC%z",
    "%d.%m.%Y %H:%M:%S %z",
    "%Y-%m-%d %H:%M:%S UTC%z",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%SZ",
    "%d %b %Y %H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%m/%d/%Y %H:%M:%S",
    "%B %d, %Y %H:%M:%S",
    "%b %d, %Y %H:%M:%S",
]


def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[archive {ts}] {msg}", file=sys.stderr)


def error(msg: str):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[archive {ts} ERROR] {msg}", file=sys.stderr)


# ── Source detection ─────────────────────────────────────────────────────

def normalize_channel_name(title: str) -> str:
    """Normalize a channel display title to a source_id."""
    lower = title.lower().strip()
    # Strip emoji and special chars for matching
    clean = re.sub(r'[^\w\s]', '', lower)
    clean = re.sub(r'\s+', ' ', clean).strip()

    # Exact-ish match against known channels
    for key, source_id in CHANNEL_SOURCE_MAP.items():
        if key in clean or clean in key:
            return source_id

    # Fallback: slugify the title
    slug = re.sub(r'[^a-z0-9]+', '-', lower).strip('-')
    return slug if slug else "unknown-telegram-export"


def detect_source_from_html(soup) -> str:
    """Extract channel title from HTML and map to source_id."""
    title_div = soup.select_one("div.text.bold")
    if title_div:
        raw_title = title_div.get_text(strip=True)
        return normalize_channel_name(raw_title)
    return "unknown-telegram-export"


def get_channel_title(soup) -> str:
    """Extract the raw channel display title from HTML."""
    title_div = soup.select_one("div.text.bold")
    if title_div:
        return title_div.get_text(strip=True)
    return ""


# ── Timestamp parsing ────────────────────────────────────────────────────

def parse_telegram_timestamp(ts_str: str) -> str | None:
    """
    Parse a Telegram export timestamp to ISO-8601 string.
    Handles formats like: 23.05.2023 09:02:17 UTC-05:00
    """
    if not ts_str:
        return None

    ts_str = ts_str.strip()

    for fmt in TIMESTAMP_FORMATS:
        try:
            dt = datetime.strptime(ts_str, fmt)
            return dt.isoformat()
        except ValueError:
            continue

    # Try stripping timezone suffix like "UTC-05:00"
    m = re.match(r'(.+?)\s+UTC([+-]\d{2}:\d{2})', ts_str)
    if m:
        base, tz = m.group(1), m.group(2)
        try:
            dt = datetime.strptime(f"{base} {tz}", "%d.%m.%Y %H:%M:%S %z")
            return dt.isoformat()
        except ValueError:
            pass

    return None


# ── HTML parsing ─────────────────────────────────────────────────────────

def extract_messages_from_file(file_path: str) -> list[dict]:
    """
    Parse a Telegram HTML export file and extract messages.
    Returns list of dicts with keys:
      raw_message_id, timestamp_iso, from_name, body_text, reactions
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        error("BeautifulSoup4 not installed. Run: pip install beautifulsoup4")
        return []

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        error(f"Cannot read {file_path}: {e}")
        return []

    soup = BeautifulSoup(content, "html.parser")
    messages = []

    msg_divs = soup.select("div.message.default.clearfix")
    if not msg_divs:
        # Fallback: try any div.message
        msg_divs = soup.select("div.message")
        msg_divs = [d for d in msg_divs if "service" not in d.get("class", [])]

    for div in msg_divs:
        try:
            msg_id = div.get("id", "")
            raw_id = msg_id.replace("message", "").strip()

            # Timestamp from pull_right date details
            date_div = div.select_one("div.pull_right.date.details")
            if date_div:
                ts_raw = date_div.get("title", "")
            else:
                ts_raw = ""

            ts_iso = parse_telegram_timestamp(ts_raw)

            # From name
            from_div = div.select_one("div.from_name")
            from_name = from_div.get_text(strip=True) if from_div else ""

            # Body text
            text_div = div.select_one("div.text")
            body_text = ""
            if text_div:
                body_text = text_div.get_text("\n", strip=True)
                # Unescape HTML entities
                body_text = ht.unescape(body_text)

            # Skip service messages with no text and no media
            if not body_text:
                continue

            # Reactions
            reactions = {}
            reactions_span = div.select_one("span.reactions")
            if reactions_span:
                for react in reactions_span.select("span.reaction"):
                    emoji_el = react.select_one("span.emoji")
                    count_el = react.select_one("span.count")
                    if emoji_el and count_el:
                        emoji = emoji_el.get_text(strip=True)
                        try:
                            count = int(count_el.get_text(strip=True))
                            reactions[emoji] = count
                        except ValueError:
                            pass

            messages.append({
                "raw_message_id": raw_id,
                "timestamp_iso": ts_iso,
                "from_name": from_name,
                "body_text": body_text,
                "reactions": reactions,
            })

        except Exception as e:
            error(f"Error parsing message in {file_path}: {e}")
            continue

    return messages


# ── Symbol extraction ────────────────────────────────────────────────────

def extract_symbols(text: str) -> list[str]:
    """Extract unique uppercase crypto symbols from text."""
    matches = CRYPTO_SYMBOL_RE.findall(text)
    seen = set()
    symbols = []
    for sym in matches:
        upper = sym.upper()
        if upper not in seen:
            seen.add(upper)
            symbols.append(upper)
    return symbols


# ── Headline extraction ──────────────────────────────────────────────────

def extract_headline(text: str) -> str:
    """Extract first 120 chars or a meaningful title from message text."""
    if not text:
        return ""

    # Take first 120 chars, cleaned
    first_line = text.split("\n")[0].strip()
    # Strip bold/formatting remnants
    first_line = re.sub(r'<[^>]+>', '', first_line)
    headline = first_line[:120]

    # If first line is very short, take more from the body
    if len(headline) < 20 and len(text) > 20:
        headline = text[:120]

    return headline


# ── Dedup (archive store, never expires) ─────────────────────────────────

def load_archive_dedup_store() -> dict:
    """Load the archive dedup store (hash → True dict)."""
    try:
        with open(ARCHIVE_DEDUP_PATH) as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        return {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_archive_dedup_store(store: dict):
    """Atomically persist the archive dedup store."""
    os.makedirs(os.path.dirname(ARCHIVE_DEDUP_PATH), exist_ok=True)
    tmp = ARCHIVE_DEDUP_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(store, f)
    os.replace(tmp, ARCHIVE_DEDUP_PATH)


def compute_archive_dedup_key(source_id: str, raw_message_id: str, body: str) -> str:
    """
    SHA256 of (source_id + raw_message_id + body[:200]) truncated to 16 chars.
    """
    raw = f"{source_id}:{raw_message_id}:{body[:200]}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def filter_dedup(events: list[dict], store: dict) -> tuple[list[dict], int, dict]:
    """
    Filter events against the dedup store.
    Returns (new_events, dup_count, updated_store).
    """
    new_events = []
    dup_count = 0
    new_hashes = {}

    for ev in events:
        source_id = ev["source_id"]
        raw_message_id = ev["provenance"]["raw_message_id"]
        body = ev["payload"]["body"]
        key = compute_archive_dedup_key(source_id, raw_message_id, body)

        if key in store:
            dup_count += 1
            continue

        new_hashes[key] = True
        new_events.append(ev)

    # Merge new hashes into store (in-memory copy)
    merged = dict(store)
    merged.update(new_hashes)
    return new_events, dup_count, merged


# ── Signal contract normalization ────────────────────────────────────────

def normalize_messages(
    raw_messages: list[dict],
    source_id: str,
    channel_title: str,
    source_file: str,
    file_hash: str,
) -> list[dict]:
    """
    Convert raw parsed messages to signal contract events.
    """
    confidence = CHANNEL_BASELINES.get(source_id, DEFAULT_BASELINE)
    events = []

    for msg in raw_messages:
        body = msg["body_text"]
        if not body:
            continue

        symbols = extract_symbols(body)
        headline = extract_headline(body)

        events.append({
            "source_id": source_id,
            "event_type": "telegram_post",
            "timestamp": msg["timestamp_iso"] or datetime.now(timezone.utc).isoformat(),
            "payload": {
                "headline": headline,
                "body": body,
                "symbols": symbols,
                "metrics": {
                    "views": 0,
                    "replies": 0,
                    "forwards": 0,
                    "reactions": msg["reactions"],
                },
            },
            "confidence": confidence,
            "provenance": {
                "source_url": source_id,
                "raw_message_id": msg["raw_message_id"],
                "source_file": source_file,
                "channel_title": channel_title,
            },
        })

    return events


# ── DuckDB operations ────────────────────────────────────────────────────

def ensure_tables(con):
    """Create archive tables if they don't exist."""
    con.execute("""
        CREATE TABLE IF NOT EXISTS archive_batches (
            batch_id VARCHAR PRIMARY KEY,
            source_file VARCHAR,
            channel_name VARCHAR,
            message_count INTEGER,
            inserted_count INTEGER,
            duplicate_count INTEGER,
            parse_error_count INTEGER,
            file_hash VARCHAR,
            processed_at TIMESTAMP DEFAULT now()
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS archive_messages (
            message_id VARCHAR PRIMARY KEY,
            source_id VARCHAR NOT NULL,
            event_type VARCHAR DEFAULT 'telegram_post',
            event_ts TIMESTAMP NOT NULL,
            headline VARCHAR,
            body TEXT,
            symbols VARCHAR[],
            metrics JSON,
            confidence DOUBLE,
            provenance JSON,
            ingested_at TIMESTAMP DEFAULT now(),
            batch_id VARCHAR
        )
    """)


def compute_batch_id(source_file: str, file_hash: str) -> str:
    """Generate a deterministic batch_id from source file and hash."""
    raw = f"{source_file}:{file_hash}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def file_already_processed(con, file_hash: str) -> bool:
    """Check if a file hash has already been processed."""
    try:
        result = con.execute(
            "SELECT COUNT(*) FROM archive_batches WHERE file_hash = ?",
            [file_hash],
        ).fetchone()
        return result[0] > 0
    except Exception:
        return False


def list_processed_files(con) -> set:
    """Return set of file hashes that have been processed."""
    try:
        rows = con.execute("SELECT file_hash FROM archive_batches").fetchall()
        return {r[0] for r in rows}
    except Exception:
        return set()


def insert_events(con, events: list[dict], batch_id: str) -> int:
    """Bulk insert events into archive_messages. Returns inserted count."""
    inserted = 0
    for ev in events:
        message_id = hashlib.sha256(
            f"{ev['source_id']}:{ev['provenance']['raw_message_id']}:{ev['timestamp']}".encode()
        ).hexdigest()[:16]

        try:
            # Parse ISO timestamp to datetime object for DuckDB
            ts_str = ev["timestamp"]
            try:
                ts_dt = datetime.fromisoformat(ts_str)
            except ValueError:
                ts_dt = datetime.now(timezone.utc)

            # Build DuckDB-compatible arrays
            symbols_list = ev["payload"]["symbols"]

            # Build metrics as JSON string
            metrics_json = json.dumps(ev["payload"]["metrics"])

            # Build provenance as JSON string
            provenance_json = json.dumps(ev["provenance"])

            con.execute(
                """INSERT OR IGNORE INTO archive_messages
                   (message_id, source_id, event_type, event_ts, headline, body,
                    symbols, metrics, confidence, provenance, ingested_at, batch_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now(), ?)""",
                [
                    message_id,
                    ev["source_id"],
                    ev["event_type"],
                    ts_dt,
                    ev["payload"]["headline"],
                    ev["payload"]["body"],
                    symbols_list,
                    metrics_json,
                    ev["confidence"],
                    provenance_json,
                    batch_id,
                ],
            )
            inserted += 1
        except Exception as e:
            error(f"Insert failed for message {message_id}: {e}")

    return inserted


def record_batch(
    con,
    batch_id: str,
    source_file: str,
    channel_name: str,
    message_count: int,
    inserted_count: int,
    duplicate_count: int,
    parse_error_count: int,
    file_hash: str,
):
    """Record batch metadata in archive_batches."""
    con.execute(
        """INSERT OR REPLACE INTO archive_batches
           (batch_id, source_file, channel_name, message_count, inserted_count,
            duplicate_count, parse_error_count, file_hash, processed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, now())""",
        [
            batch_id,
            source_file,
            channel_name,
            message_count,
            inserted_count,
            duplicate_count,
            parse_error_count,
            file_hash,
        ],
    )


def get_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of file contents."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


# ── CLI actions ──────────────────────────────────────────────────────────

def action_list(args):
    """List all HTML files in inbound/ and their processing status."""
    inbound = Path(INBOUND_DIR)
    if not inbound.exists():
        log(f"Inbound directory not found: {INBOUND_DIR}")
        return

    try:
        import duckdb
        con = duckdb.connect(DB_PATH)
        ensure_tables(con)
        processed_hashes = list_processed_files(con)
        con.close()
    except ImportError:
        log("DuckDB not available; running without DB checks")
        processed_hashes = set()

    html_files = sorted(inbound.glob("*.html"))
    if not html_files:
        log("No HTML files found in inbound directory")
        return

    print(f"{'STATUS':<12} {'SIZE':>8} {'CHANNEL':<30} {'FILE':<50}")
    print(f"{'-'*12} {'-'*8} {'-'*30} {'-'*50}")

    for fp in html_files:
        fhash = get_file_hash(str(fp.resolve()))
        status = "PROCESSED" if fhash in processed_hashes else "NEW"
        size = fp.stat().st_size
        # Quick channel title extraction
        channel = "unknown"
        try:
            content = fp.read_text(encoding="utf-8", errors="replace")
            m = re.search(r'class="text bold">([^<]+)', content)
            if m:
                channel = m.group(1).strip()
        except Exception:
            pass
        print(f"{status:<12} {size:>8} {channel:<30} {fp.name:<50}")


def action_summarize(args):
    """Show stats from archive_messages table."""
    try:
        import duckdb
    except ImportError:
        error("DuckDB not installed")
        return

    con = duckdb.connect(DB_PATH)
    ensure_tables(con)

    try:
        # Total count
        total = con.execute("SELECT COUNT(*) FROM archive_messages").fetchone()[0]
        print(f"\n📊 Archive Messages Summary")
        print(f"{'='*50}")
        print(f"Total messages:  {total}")

        # Per-source breakdown
        rows = con.execute(
            """SELECT source_id, COUNT(*) as cnt, MIN(event_ts) as first_seen,
                      MAX(event_ts) as last_seen
               FROM archive_messages
               GROUP BY source_id
               ORDER BY cnt DESC"""
        ).fetchall()

        if rows:
            print(f"\n{'SOURCE':<25} {'COUNT':>8} {'FIRST':<22} {'LAST':<22}")
            print(f"{'-'*25} {'-'*8} {'-'*22} {'-'*22}")
            for sid, cnt, first, last in rows:
                f_str = str(first)[:19] if first else "N/A"
                l_str = str(last)[:19] if last else "N/A"
                print(f"{sid:<25} {cnt:>8} {f_str:<22} {l_str:<22}")

        # Batch summary
        batch_count = con.execute("SELECT COUNT(*) FROM archive_batches").fetchone()[0]
        total_inserted = con.execute(
            "SELECT COALESCE(SUM(inserted_count), 0) FROM archive_batches"
        ).fetchone()[0]
        total_dupes = con.execute(
            "SELECT COALESCE(SUM(duplicate_count), 0) FROM archive_batches"
        ).fetchone()[0]
        print(f"\nBatch files:     {batch_count}")
        print(f"Total inserted:  {total_inserted}")
        print(f"Total duplicates:{total_dupes}")

    except Exception as e:
        error(f"Summarize error: {e}")
    finally:
        con.close()


def action_dry_run(args):
    """Dry-run: parse files and count messages without inserting."""
    inbound = Path(INBOUND_DIR)
    if not inbound.exists():
        error(f"Inbound directory not found: {INBOUND_DIR}")
        return

    try:
        import duckdb
        con = duckdb.connect(DB_PATH)
        ensure_tables(con)
        processed_hashes = list_processed_files(con) if not args.force else set()
        con.close()
    except ImportError:
        processed_hashes = set()

    html_files = sorted(inbound.glob("*.html"))
    if not html_files:
        log("No HTML files found")
        return

    total_messages = 0
    total_new = 0
    total_duplicates = 0
    file_details = []

    for fp in html_files:
        fhash = get_file_hash(str(fp.resolve()))

        if fhash in processed_hashes:
            status = "SKIP (processed)"
            file_details.append({"file": fp.name, "status": status, "msgs": 0, "new": 0, "dupes": 0})
            continue

        messages = extract_messages_from_file(str(fp.resolve()))
        if not messages:
            status = "SKIP (no messages)"
            file_details.append({"file": fp.name, "status": status, "msgs": 0, "new": 0, "dupes": 0})
            continue

        # Get channel info
        content = fp.read_text(encoding="utf-8", errors="replace")
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, "html.parser")
        source_id = detect_source_from_html(soup)
        channel_title = get_channel_title(soup)

        # Normalize
        events = normalize_messages(messages, source_id, channel_title, fp.name, fhash)

        # Dedup check
        store = load_archive_dedup_store()
        new_events, dup_count, _ = filter_dedup(events, store)

        total_messages += len(messages)
        total_new += len(new_events)
        total_duplicates += dup_count

        file_details.append({
            "file": fp.name,
            "status": f"{len(new_events)} new / {dup_count} dup",
            "msgs": len(messages),
            "new": len(new_events),
            "dupes": dup_count,
        })

    print(f"\n🔍 Dry Run — Archive Ingest")
    print(f"{'='*60}")
    print(f"{'FILE':<55} {'MSGS':>6} {'NEW':>6} {'DUP':>6}")
    print(f"{'-'*55} {'-'*6} {'-'*6} {'-'*6}")
    for fd in file_details:
        print(f"{fd['file']:<55} {fd['msgs']:>6} {fd['new']:>6} {fd['dupes']:>6}")
    print(f"{'='*60}")
    print(f"Total files:    {len(file_details)}")
    print(f"Total messages: {total_messages}")
    print(f"Would insert:   {total_new}")
    print(f"Would dedup:    {total_duplicates}")

    # Channel stats
    from collections import Counter
    chan_counter = Counter()
    inbound_path = Path(INBOUND_DIR)
    for fp in sorted(inbound_path.glob("*.html")):
        fhash = get_file_hash(str(fp.resolve()))
        if fhash in processed_hashes and not args.force:
            continue
        content = fp.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(content, "html.parser")
        source_id = detect_source_from_html(soup)
        msgs = extract_messages_from_file(str(fp.resolve()))
        chan_counter[source_id] += len(msgs)

    if chan_counter:
        print(f"\nChannel breakdown:")
        for cid, cnt in chan_counter.most_common():
            baseline = CHANNEL_BASELINES.get(cid, DEFAULT_BASELINE)
            inst_est = int(cnt * baseline)
            print(f"  {cid:<25} {cnt:>6} msgs  (baseline: {baseline:.2f}, ~{inst_est} signal)")


def action_ingest(args):
    """Main ingest: process files, normalize, dedup, insert into DuckDB."""
    try:
        import duckdb
    except ImportError:
        error("DuckDB not installed. Run: pip install duckdb")
        return 1

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        error("BeautifulSoup4 not installed. Run: pip install beautifulsoup4")
        return 1

    inbound = Path(INBOUND_DIR)
    if not inbound.exists():
        error(f"Inbound directory not found: {INBOUND_DIR}")
        return 1

    # Connect and ensure tables
    con = duckdb.connect(DB_PATH)
    ensure_tables(con)

    processed_hashes = list_processed_files(con) if not args.force else set()

    # Determine which files to process
    if args.file:
        fp = Path(args.file)
        if not fp.exists():
            error(f"File not found: {args.file}")
            return 1
        if not fp.name.endswith(".html"):
            error(f"Not an HTML file: {args.file}")
            return 1
        html_files = [fp]
    else:
        html_files = sorted(inbound.glob("*.html"))

    if not html_files:
        log("No HTML files to process")
        return 0

    # Load archive dedup store once
    dedup_store = load_archive_dedup_store()

    total_files = 0
    total_messages = 0
    total_inserted = 0
    total_duplicates = 0
    total_parse_errors = 0

    for fp in html_files:
        fhash = get_file_hash(str(fp.resolve()))

        if fhash in processed_hashes:
            log(f"SKIP: {fp.name} (already processed, hash: {fhash[:12]}...)")
            continue

        total_files += 1
        log(f"Processing: {fp.name} ({fp.stat().st_size:,} bytes)")

        # Parse HTML
        messages = extract_messages_from_file(str(fp.resolve()))
        if not messages:
            log(f"  No messages extracted from {fp.name}")
            total_parse_errors += 1
            continue

        # Get channel info
        content = fp.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(content, "html.parser")
        source_id = detect_source_from_html(soup)
        channel_title = get_channel_title(soup)

        log(f"  Channel: {channel_title} → source_id: {source_id}")
        log(f"  Extracted {len(messages)} raw messages")

        # Normalize to signal contract
        events = normalize_messages(messages, source_id, channel_title, fp.name, fhash)
        log(f"  Normalized {len(events)} events")

        # Dedup
        new_events, dup_count, updated_store = filter_dedup(events, dedup_store)
        dedup_store = updated_store

        log(f"  After dedup: {len(new_events)} new, {dup_count} duplicates")

        if not new_events:
            # Still record the batch with 0 insertions
            batch_id = compute_batch_id(str(fp.resolve()), fhash)
            record_batch(con, batch_id, fp.name, channel_title, len(messages), 0, dup_count, 0, fhash)
            total_duplicates += dup_count
            continue

        # Batch ID
        batch_id = compute_batch_id(str(fp.resolve()), fhash)

        # Insert into DuckDB
        inserted = insert_events(con, new_events, batch_id)
        inserted = len(new_events)  # INSERT OR IGNORE, count what we attempted

        # Record batch
        record_batch(con, batch_id, fp.name, channel_title, len(messages), inserted, dup_count, 0, fhash)

        total_messages += len(messages)
        total_inserted += inserted
        total_duplicates += dup_count

        log(f"  Inserted {inserted} messages into archive_messages")

    # Persist dedup store
    save_archive_dedup_store(dedup_store)
    log(f"Dedup store saved ({len(dedup_store)} entries)")

    con.close()

    # Summary
    log(f"{'='*50}")
    log(f"Summary: {total_files} files, {total_messages} messages")
    log(f"  Inserted: {total_inserted}")
    log(f"  Duplicates: {total_duplicates}")
    log(f"  Parse errors: {total_parse_errors}")

    return 0


# ── Main entry point ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Archive Batch Processor — ingest Telegram HTML exports into the signal pipeline"
    )

    # Action group (mutually exclusive-ish)
    action_group = parser.add_argument_group("actions")
    action_group.add_argument("--file", type=str, help="Process a single HTML file")
    action_group.add_argument("--force", action="store_true", help="Reprocess even already-processed files")
    action_group.add_argument("--dry-run", action="store_true", help="Count messages without inserting")
    action_group.add_argument("--list", action="store_true", help="List files and their status")
    action_group.add_argument("--summarize", action="store_true", help="Show stats from archive_messages table")

    args = parser.parse_args()

    # Route to appropriate action
    if args.list:
        action_list(args)
    elif args.summarize:
        action_summarize(args)
    elif args.dry_run:
        action_dry_run(args)
    elif args.file or True:  # Default: ingest
        return action_ingest(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())