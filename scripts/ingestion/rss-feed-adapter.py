#!/usr/bin/env python3
"""Generic RSS Feed Adapter — fetches RSS, normalizes to signal contract, writes JSONL.
Usage:
  python3 rss-feed-adapter.py --source cointelegraph
  python3 rss-feed-adapter.py --source coindesk
  python3 rss-feed-adapter.py --source techcrunch
  python3 rss-feed-adapter.py --source all
  cat /path/to/file.jsonl | python3 rss-feed-adapter.py --stdin  # passthrough route
"""

import json, os, re, sys, time, html as ht
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

BASE = Path("/home/synczus/kestrel")
OUT_DIR = BASE / "pulse"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"

# ── Source Configurations ──────────────────────────────────────────────

SOURCES = {
    "cointelegraph": {
        "name": "cointelegraph",
        "rss_url": "https://cointelegraph.com/rss",
        "baseline": 0.25,
        "keyword_tags": ["BTC", "ETH", "CRYPTO"],
        "event_type": "crypto_news",
        "cron_schedule": "0 */4 * * *",
    },
    "coindesk": {
        "name": "coindesk",
        "rss_url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "baseline": 0.25,
        "keyword_tags": ["BTC", "ETH", "CRYPTO"],
        "event_type": "crypto_news",
        "cron_schedule": "0 */4 * * *",
    },
    "techcrunch": {
        "name": "techcrunch",
        "rss_url": "https://techcrunch.com/feed/",
        "baseline": 0.20,
        "keyword_tags": ["AI", "BIGTECH"],
        "event_type": "tech_news",
        "cron_schedule": "0 */4 * * *",
    },
}

def strip_html(text: str) -> str:
    """Remove HTML tags, including embedded image tags and cruft."""
    if not text:
        return ""
    # Remove CDATA
    text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text, flags=re.DOTALL)
    # Strip all HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Unescape HTML entities
    text = ht.unescape(text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def fetch_rss(source_config: dict) -> list[dict]:
    """Fetch RSS XML, parse items, return list of raw item dicts."""
    url = source_config["rss_url"]
    name = source_config["name"]
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        data = urlopen(req, timeout=15).read()
    except Exception as e:
        print(f"[{name}] RSS fetch failed: {e}", file=sys.stderr)
        return []

    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        print(f"[{name}] RSS parse failed: {e}", file=sys.stderr)
        return []

    # Handle RSS 2.0 and Atom feeds
    items = []
    # RSS 2.0: channel > item
    for item in root.findall(".//channel/item") or root.findall(".//item"):
        items.append(item)
    # Atom: entry elements (fallback if RSS items empty)
    if not items:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = root.findall(".//atom:entry", ns) or root.findall(".//entry")

    parsed = []
    for item in items:
        # Extract common fields
        title = item.findtext("title", "")
        link_elem = item.find("link")
        link = ""
        if link_elem is not None:
            link = link_elem.text or link_elem.get("href", "")
        description = item.findtext("description", "")
        pubdate = item.findtext("pubDate", "")
        creator = item.findtext("dc:creator", "") or item.findtext("{http://purl.org/dc/elements/1.1/}creator", "")
        # Atom format
        if not title:
            title = item.findtext("{http://www.w3.org/2005/Atom}title", "")
        if not link:
            link_elem = item.find("{http://www.w3.org/2005/Atom}link")
            if link_elem is not None:
                link = link_elem.get("href", "")
        summary = item.findtext("{http://www.w3.org/2005/Atom}summary", "")
        if not description:
            description = summary

        parsed.append({
            "title": title.strip() if title else "",
            "link": link.strip() if link else "",
            "description": strip_html(description),
            "pubDate": pubdate.strip() if pubdate else "",
            "creator": creator.strip() if creator else "",
        })

    return parsed


YMD_PATTERN = re.compile(r'(\d{4})-(\d{2})-(\d{2})')

def parse_timestamp(pubdate_str: str) -> int:
    """Parse RSS pubDate or Atom date into nanosecond timestamp."""
    if not pubdate_str:
        return int(time.time() * 1_000_000_000)

    # Try common RSS formats
    for fmt in [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S.%fZ",
    ]:
        try:
            dt = datetime.strptime(pubdate_str.strip(), fmt)
            return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1_000_000_000)
        except ValueError:
            continue

    # Falling back to now
    return int(time.time() * 1_000_000_000)


def detect_symbols(title: str, description: str) -> list[str]:
    """Detect ticker symbols from title + description text."""
    text = (title + " " + description).lower()
    symbols = []
    seen = set()

    checks = [
        (r'\bbitcoin\b', "BTC"),
        (r'\bbtc\b', "BTC"),
        (r'\bethereum\b', "ETH"),
        (r'\beth\b', "ETH"),
        (r'\bsolana\b', "SOL"),
        (r'\bsol\b', "SOL"),
        (r'\bcrypto\b', "CRYPTO"),
        (r'\baltcoin\b', "CRYPTO"),
        (r'\bdefi\b', "CRYPTO"),
        (r'\bai\b', "AI"),
        (r'\bllm\b', "AI"),
        (r'\bgpt\b', "AI"),
        (r'\bclaude\b', "AI"),
        (r'\bmachine learning\b', "AI"),
        (r'\bdeepseek\b', "AI"),
        (r'\bapple\b', "BIGTECH"),
        (r'\bgoogle\b', "BIGTECH"),
        (r'\bmicrosoft\b', "BIGTECH"),
        (r'\bmeta\b', "BIGTECH"),
        (r'\bnvidia\b', "BIGTECH"),
        (r'\bamazon\b', "BIGTECH"),
        (r'\bspacex\b', "BIGTECH"),
        (r'\btesla\b', "BIGTECH"),
        (r'\bopenai\b', "AI"),
        (r'\banthropic\b', "AI"),
        (r'\bxrp\b', "CRYPTO"),
        (r'\bdoge\b', "CRYPTO"),
        (r'\bcardano\b', "CRYPTO"),
    ]

    for pattern, sym in checks:
        if re.search(pattern, text) and sym not in seen:
            symbols.append(sym)
            seen.add(sym)

    return symbols


def normalize(raw_items: list[dict], source_config: dict) -> list[dict]:
    """Convert raw RSS items to signal contract events."""
    name = source_config["name"]
    event_type = source_config["event_type"]
    tag_list = source_config["keyword_tags"]
    events = []

    for item in raw_items:
        title = item["title"]
        description = item["description"]
        link = item["link"]
        pubdate = item["pubDate"]

        if not title:
            continue

        # Compute magnitude: 0.30 for meaningful descriptions, 0.15 for minimal/no desc
        desc_words = len(description.split()) if description else 0
        magnitude = 0.30 if desc_words > 10 else 0.15

        # Detect symbols
        symbols = detect_symbols(title, description)

        # Build headline
        headline = f"[{event_type.replace('_',' ').title()}] {title}"
        if len(headline) > 200:
            headline = headline[:200]

        # Build body with full description
        body_parts = {"title": title}
        if description:
            body_parts["summary"] = description[:1000]
        if item["creator"]:
            body_parts["author"] = item["creator"]
        if link:
            body_parts["url"] = link
        body = json.dumps(body_parts)

        # Build raw_message_id
        raw_id = f"{name}:{abs(hash(title)) % 10**9}"
        if pubdate:
            raw_id = f"{name}:{pubdate}:{abs(hash(title)) % 10**9}"

        events.append({
            "source_id": name,
            "event_type": event_type,
            "timestamp": parse_timestamp(pubdate),
            "payload": {
                "headline": headline,
                "body": body,
                "symbols": symbols,
                "metrics": {
                    "confidence": source_config["baseline"],
                    "magnitude": round(magnitude, 2),
                    "velocity": "steady",
                }
            },
            "provenance": {
                "source_url": link,
                "raw_message_id": raw_id,
                "verified": False,
                "verified_by": f"rss-{name}"
            }
        })

    return events


def write_output(events: list[dict], source_name: str):
    """Write events to per-source JSONL file."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{source_name}-inbox.jsonl"
    with open(out_path, "w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")
    return out_path


def run_source(source_name: str, item_limit: int = 50, stats: bool = False):
    """Run the full pipeline for one source."""
    if source_name not in SOURCES:
        print(f"Unknown source: {source_name}", file=sys.stderr)
        print(f"Available: {list(SOURCES.keys())}", file=sys.stderr)
        return 1

    config = SOURCES[source_name]
    name = config["name"]

    print(f"[{name}] Fetching RSS from {config['rss_url']}...", file=sys.stderr)
    raw_items = fetch_rss(config)

    if not raw_items:
        print(f"[{name}] No items found", file=sys.stderr)
        return 1

    if len(raw_items) > item_limit:
        raw_items = raw_items[:item_limit]
    print(f"[{name}] {len(raw_items)} raw items fetched", file=sys.stderr)

    events = normalize(raw_items, config)
    if not events:
        print(f"[{name}] No events generated", file=sys.stderr)
        return 1

    out_path = write_output(events, name)
    print(f"[{name}] {len(events)} events → {out_path}", file=sys.stderr)

    if stats:
        sources = {}
        for e in events:
            et = e["event_type"]
            sources[et] = sources.get(et, 0) + 1
        symbols = set()
        for e in events:
            symbols.update(e["payload"]["symbols"])

        print(f"\n📡 RSS Feed: {name}")
        print(f"   Items: {len(events)}")
        print(f"   Event types: {sources}")
        print(f"   Symbols: {sorted(symbols) if symbols else 'none'}")
        confs = [e["payload"]["metrics"]["confidence"] for e in events]
        if confs:
            print(f"   Baseline confidence: {min(confs):.2f}–{max(confs):.2f}")
        print(f"   Output: {out_path}")

    return 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="RSS Feed Signal Adapter")
    parser.add_argument("--source", default="cointelegraph",
                        choices=list(SOURCES.keys()) + ["all"],
                        help="Source to scrape (default: cointelegraph, use 'all' for all sources)")
    parser.add_argument("--limit", type=int, default=50,
                        help="Max items per source (default: 50)")
    parser.add_argument("--stats", action="store_true",
                        help="Print stats summary")
    args = parser.parse_args()

    if args.source == "all":
        exit_code = 0
        for src in SOURCES:
            ec = run_source(src, args.limit, args.stats)
            if ec != 0:
                exit_code = ec
        return exit_code
    else:
        return run_source(args.source, args.limit, args.stats)


if __name__ == "__main__":
    sys.exit(main())