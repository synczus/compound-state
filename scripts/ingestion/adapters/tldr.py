#!/usr/bin/env python3
"""
TLDR Newsletter Scraper v0.3
Fetches https://tldr.tech/api/latest/tech, extracts article content using
readability-lxml, normalizes each article into event_shape format.

Usage:
  python3 scripts/ingestion/adapters/tldr.py --latest
  python3 scripts/ingestion/adapters/tldr.py --date 2026-06-05
"""
import hashlib
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from readability import Document

KESTREL_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
INBOX_DIR = os.path.join(KESTREL_ROOT, "ingestion", "inbox")

# Match: [Headline (read time)](url) pattern from markdown
ARTICLE_RE = re.compile(
    r'\[([^\]]+?)\s*\((\d+ minute read|Sponsor|GitHub Repo)\)\]\((\S+)\)',
    re.IGNORECASE,
)
# Fallback: just [text](url) with no read time
FALLBACK_RE = re.compile(
    r'\[([^\]]{15,})\]\s*\((https?://[^\s)]+)\)',
    re.IGNORECASE,
)

_EVENT_KW = {
    "ai": ("tech_ai", 0.25), "llm": ("tech_ai", 0.25), "gpt": ("tech_ai", 0.25),
    "claude": ("tech_ai", 0.25), "openai": ("tech_ai", 0.3), "anthropic": ("tech_ai", 0.3),
    "apple": ("tech_product", 0.15), "google": ("tech_product", 0.15),
    "microsoft": ("tech_product", 0.15), "meta": ("tech_product", 0.15),
    "bitcoin": ("crypto", 0.35), "crypto": ("crypto", 0.25),
    "ethereum": ("crypto", 0.25), "sec": ("regulatory", 0.25),
    "regulation": ("regulatory", 0.25), "funding": ("startup_funding", 0.3),
    "series a": ("startup_funding", 0.3), "series b": ("startup_funding", 0.3),
    "ipo": ("startup_funding", 0.35), "acquisition": ("market_corporate", 0.3),
    "layoff": ("market_corporate", 0.25), "breach": ("tech_security", 0.4),
    "hack": ("tech_security", 0.45), "vulnerability": ("tech_security", 0.25),
    "chip": ("tech_hardware", 0.2), "nvidia": ("tech_hardware", 0.3),
    "quantum": ("tech_hardware", 0.3), "robot": ("tech_robotics", 0.25),
    "autonomous": ("tech_robotics", 0.25), "space": ("tech_space", 0.2),
    "climate": ("tech_climate", 0.2), "open source": ("tech_oss", 0.15),
}


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_articles(html: str) -> list[dict]:
    """Use readability to extract main content, then find articles."""
    doc = Document(html)
    title = doc.title()
    content = doc.summary()

    # Parse extracted HTML for <a> tags containing headlines
    # Format: <a href="url"><h3>Headline (N minute read)</h3></a>
    articles = []
    a_tag_re = re.compile(r'<a\s+[^>]*href="([^"]+)"[^>]*>(?:<[^>]+>)?([^<]+)(?:</[^>]+>)?</a>', re.I)

    for match in a_tag_re.finditer(content):
        url = match.group(1).strip()
        headline = match.group(2).strip()

        # Skip sponsors and navigation
        if not url.startswith('http'):
            continue
        if 'sponsor' in headline.lower() or 'Sponsor' in headline:
            continue
        if len(headline) < 15:
            continue

        articles.append((headline, url))

    # Deduplicate by headline
    seen = set()
    result = []
    for headline, url in articles:
        h = headline.strip().lower()
        if h and h not in seen and len(headline) > 10:
            seen.add(h)
            # Classify
            lower = headline.lower()
            best_type, best_boost = "tech_news", 0.0
            for kw, (etype, boost) in _EVENT_KW.items():
                if kw in lower and boost > best_boost:
                    best_type = etype
                    best_boost = boost

            # Velocity
            urgency = {"breaking", "new", "just", "launch", "announces", "releases"}
            velocity = "rising" if set(lower.split()[:10]) & urgency else "steady"

            # Symbols
            syms = re.findall(r'\b([A-Z]{2,6})\b', headline)
            noise = {"THE", "FOR", "AND", "WAS", "NOT", "YOU", "ALL",
                     "ITS", "FROM", "THAT", "THIS", "WITH", "WILL",
                     "HAVE", "BEEN", "NEWS", "JUST", "NOW", "SERIES"}
            symbols = [s for s in syms if s not in noise and len(s) > 1][:5]

            result.append({
                "headline": headline,
                "url": url,
                "event_type": best_type,
                "magnitude": round(best_boost, 3),
                "velocity": velocity,
                "symbols": symbols,
            })

    return result


def write_to_inbox(articles: list[dict], date_str: str) -> int:
    os.makedirs(INBOX_DIR, exist_ok=True)
    count = 0
    for art in articles:
        text = f"{art['headline']} — {art['url']}"
        canonical = f"tldr:{date_str}:{hash(art['headline'])}"
        provenance_hash = hashlib.sha256(canonical.encode()).hexdigest()[:16]
        event = {
            "source_id": "tldr",
            "event_type": art["event_type"],
            "timestamp": f"{date_str}T12:00:00Z",
            "payload": {
                "headline": art["headline"][:200],
                "body": text,
                "symbols": art["symbols"],
                "metrics": {
                    "confidence": None,
                    "magnitude": art["magnitude"],
                    "velocity": art["velocity"],
                },
            },
            "provenance_hash": provenance_hash,
        }
        with open(os.path.join(INBOX_DIR, f"tldr-{date_str}-{count:03d}.json"), "w") as f:
            json.dump(event, f)
        count += 1
    return count


def main():
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if "--date" in sys.argv:
        idx = sys.argv.index("--date")
        date_str = sys.argv[idx + 1]
        y, m, d = date_str.split("-")
        url = f"https://tldr.tech/tech/{date_str}"
    else:
        url = "https://tldr.tech/api/latest/tech"  # redirects to latest

    print(f"[tldr] Fetching: {url}", file=sys.stderr)
    html = fetch_html(url)
    print(f"[tldr] Got {len(html)} bytes", file=sys.stderr)

    articles = extract_articles(html)
    if not articles:
        print("[tldr] No articles found. Site may have changed.", file=sys.stderr)
        return

    print(f"[tldr] Found {len(articles)} articles", file=sys.stderr)
    for a in articles[:5]:
        print(f"  • {a['event_type']}: {a['headline'][:80]}", file=sys.stderr)

    count = write_to_inbox(articles, date_str)
    print(f"[tldr] {count} events → ingestion/inbox/", file=sys.stderr)


if __name__ == "__main__":
    main()