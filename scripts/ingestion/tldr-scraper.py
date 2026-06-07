#!/usr/bin/env python3
"""TLDR Newsletter Scraper v4 — uses HTML extraction + text parsing.
Daily signal extraction to signal contract.
Output: JSONL events ready for ingestion router.
"""

import json, os, re, sys, time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from pathlib import Path

BASE = Path("/home/synczus/kestrel")
OUT_DIR = BASE / "pulse"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"

SECTION_MAP = {
    "big tech & startups": "tech_news",
    "science & futuristic technology": "science_news",
    "programming, design & data science": "dev_news",
    "miscellaneous": "general_news",
    "quick links": "quick_links",
}

CONF_MAP = {
    "tech_news": 0.35, "science_news": 0.30,
    "dev_news": 0.40, "general_news": 0.25, "quick_links": 0.20,
}


def fetch_text(date_str: str) -> str:
    """Fetch newsletter page, strip HTML, return clean text with line breaks."""
    url = f"https://tldr.tech/tech/{date_str}"
    try:
        resp = urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=15)
        html = resp.read().decode("utf-8")
    except Exception as e:
        return ""

    # Find content-center div (contains the newsletter)
    import html as ht
    idx = html.find('content-center max-w-xl')
    if idx < 0:
        return ""

    # Locate the surrounding div
    start = html.rfind('<div', 0, idx)
    if start < 0:
        start = idx

    # Track nesting to find matching close
    depth = 0
    end = start
    for i in range(start, len(html)):
        if html[i:i+4] == '<div':
            depth += 1
        elif html[i:i+6] == '</div>':
            depth -= 1
            if depth == 0:
                end = i + 6
                break

    content = html[start:end]
    # Add newlines before block elements to preserve structure
    content = re.sub(r'</?(?:div|p|h[1-6]|li|br|section|article)[^>]*>', r'\n', content)
    # Strip remaining HTML tags
    text = re.sub(r'<[^>]+>', '', content)
    text = ht.unescape(text)
    # Clean whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n[ \t]+', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_articles(text: str) -> list[dict]:
    """Parse newsletter text into structured articles."""
    articles = []
    current_section = "general"

    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # Skip the TLDR header and subtitle
        if line.startswith("TLDR "):
            i += 1
            continue

        # Detect section: emoji alone OR emoji + section name
        # Lines like "📱" followed by "Big Tech & Startups"
        if re.match(r'^[📱🚀💻🎁⚡🌟🔄🔬💡🏢]+$', line):
            # Next line is likely the section name
            if i + 1 < len(lines):
                sec = lines[i + 1].strip().lower()
                if sec in SECTION_MAP:
                    current_section = SECTION_MAP[sec]
                    i += 2
                    continue
            i += 1
            continue

        # Also detect section directly: "Big Tech & Startups" (from emoji detection above, fallback)
        if line.lower() in SECTION_MAP:
            current_section = SECTION_MAP[line.lower()]
            i += 1
            continue

        # Skip sponsor lines, footer
        if any(s in line.lower() for s in ["sponsor", "get the most interesting",
                                            "subscribe", "privacy", "careers",
                                            "advertise", "take a closer look"]):
            i += 1
            continue

        # Detect article with read time: "Title (X minute read)"
        m = re.match(r'^(.+?)\s*\((\d+\s*minute read)\)\s*(.*)', line)
        if m:
            title = m.group(1).strip()
            read_time = m.group(2).strip()
            summary = m.group(3).strip()

            # Collect summary continuation lines
            while i + 1 < len(lines):
                nxt = lines[i + 1].strip()
                if not nxt:
                    break
                if nxt in SECTION_MAP or re.match(r'^[📱🚀💻🎁⚡🌟🔄🔬💡🏢]+$', nxt):
                    break
                if re.match(r'^.+?\(\d+\s*minute read\)', nxt):
                    break
                if any(s in nxt.lower() for s in ["tldr", "sponsor"]):
                    break
                summary += ' ' + nxt
                i += 1

            summary = re.sub(r'\s+', ' ', summary).strip()
            articles.append({
                "section": current_section,
                "title": title,
                "read_time": read_time,
                "summary": summary,
            })
            i += 1
            continue

        # Detect Quick Links (after section has been set to quick_links)
        if current_section == "quick_links" and len(line) > 15:
            articles.append({
                "section": "quick_links",
                "title": line.strip(),
                "read_time": "quick link",
                "summary": "",
            })

        i += 1

    return articles


def normalize(articles: list[dict], date_str: str) -> list[dict]:
    """Convert to signal contract events."""
    events = []
    ts_ns = int(time.time() * 1_000_000_000)
    if date_str:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            ts_ns = int(dt.replace(tzinfo=timezone.utc).timestamp() * 1_000_000_000)
        except:
            pass

    for art in articles:
        conf = CONF_MAP.get(art["section"], 0.30)
        magnitude = 0.30 if art["summary"] else 0.15

        symbols = []
        tl = art["title"].lower()
        if any(w in tl for w in ["bitcoin", "btc"]): symbols.append("BTC")
        if any(w in tl for w in ["ethereum", "eth"]): symbols.append("ETH")
        if any(w in tl for w in ["solana", "sol"]): symbols.append("SOL")
        if any(w in tl for w in ["crypto", "altcoin", "defi"]): symbols.append("CRYPTO")
        if any(w in tl for w in ["ai", "llm", "gpt", "claude", "agent", "machine learning"]): symbols.append("AI")
        if any(w in tl for w in ["apple", "google", "microsoft", "meta", "nvidia", "amazon", "spacex"]): symbols.append("BIGTECH")

        section_label = art["section"].replace("_news", "").replace("_", " ").title()
        headline = f"[{section_label}] {art['title']}"
        body = json.dumps({
            "title": art["title"],
            "summary": art["summary"][:500] if art["summary"] else "",
            "read_time": art["read_time"],
        })

        events.append({
            "source_id": "tldr",
            "event_type": art["section"],
            "timestamp": ts_ns,
            "payload": {
                "headline": headline[:200],
                "body": body,
                "symbols": symbols,
                "metrics": {
                    "confidence": round(conf, 2),
                    "magnitude": round(magnitude, 2),
                    "velocity": "steady",
                }
            },
            "provenance": {
                "source_url": f"https://tldr.tech/tech/{date_str}",
                "raw_message_id": f"tldr:{date_str}:{abs(hash(art['title'])) % 10**9}",
                "verified": False,
                "verified_by": "tldr-scraper"
            }
        })

    return events


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default="", help="YYYY-MM-DD (default: latest from RSS)")
    parser.add_argument("--output", type=Path, default=OUT_DIR / "tldr-inbox.jsonl")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--test", action="store_true", help="Print extracted text for debugging")
    args = parser.parse_args()

    if args.date:
        dates = [args.date]
    else:
        # Fetch latest date from RSS
        import xml.etree.ElementTree as ET
        try:
            r = Request("https://tldr.tech/rss", headers={"User-Agent": USER_AGENT})
            data = urlopen(r, timeout=10).read()
            root = ET.fromstring(data)
            items = root.findall(".//item")
            dates = []
            for item in items:
                pd = item.findtext("pubDate", "")
                m = re.match(r'\w+,\s+(\d+\s+\w+\s+\d+)', pd)
                if m:
                    dt = datetime.strptime(m.group(1), "%d %b %Y")
                    dates.append(dt.strftime("%Y-%m-%d"))
            if not dates:
                dates = [datetime.now(timezone.utc).strftime("%Y-%m-%d")]
        except:
            dates = [datetime.now(timezone.utc).strftime("%Y-%m-%d")]

    all_events = []
    for date_str in dates[:3]:
        text = fetch_text(date_str)
        if not text:
            print(f"  No content for {date_str}", file=sys.stderr)
            continue

        if args.test:
            print(f"\n=== {date_str} ===")
            print(text[:2000])
            print("...")

        articles = extract_articles(text)
        if not articles:
            print(f"  No articles in {date_str}", file=sys.stderr)
            continue

        events = normalize(articles, date_str)
        all_events.extend(events)
        print(f"  {date_str}: {len(articles)} articles, {len(events)} events", file=sys.stderr)

    if not all_events:
        print("No events generated", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        for ev in all_events:
            f.write(json.dumps(ev) + "\n")

    if args.stats:
        sections = {}
        for e in all_events:
            sections[e["event_type"]] = sections.get(e["event_type"], 0) + 1
        symbols = set()
        for e in all_events:
            symbols.update(e["payload"]["symbols"])
        print(f"\n📰 TLDR Scraper v4")
        print(f"   Newsletters: {len(set(dates[:3]))}")
        print(f"   Articles: {len(all_events)}")
        print(f"   Sections: {sections}")
        print(f"   Symbols: {sorted(symbols) if symbols else 'none'}")
        confs = [e["payload"]["metrics"]["confidence"] for e in all_events]
        if confs:
            print(f"   Confidence: {min(confs):.2f}–{max(confs):.2f}")
        print(f"   Output: {args.output}")
    return 0

if __name__ == "__main__":
    sys.exit(main())