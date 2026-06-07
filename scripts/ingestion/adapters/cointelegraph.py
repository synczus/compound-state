#!/usr/bin/env python3
"""Cointelegraph Telegram adapter — ingests headlines from Cointelegraph RSS feed and routes as market news."""
import sys, os, json, hashlib, re
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Try to fetch RSS
try:
    import urllib.request
    import xml.etree.ElementTree as ET
    
    feed_url = "https://cointelegraph.com/rss"
    req = urllib.request.Request(feed_url, headers={"User-Agent": "Kestrel-Signal-Pipeline/1.0"})
    resp = urllib.request.urlopen(req, timeout=15)
    xml_data = resp.read().decode("utf-8")
    
    root = ET.fromstring(xml_data)
    ns = {"rss": "http://www.w3.org/2005/Atom" if "atom" in xml_data[:500].lower() else ""}
    
    items = []
    for item in root.iter("item"):
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        pub_date = item.findtext("pubDate", "")
        description = item.findtext("description", title)
        
        if not title:
            continue
        
        # Compute content hash for dedup
        content_hash = hashlib.sha256(f"cointelegraph:{link}".encode()).hexdigest()[:16]
        
        # Classify by keywords
        keywords = {
            "bitcoin", "btc", "ethereum", "eth", "solana", "xrp", "sec", "fed",
            "regulation", "etf", "inflation", "cpi", "rate", "mining", "halving",
            "defi", "nft", "layer2", "l2", "rwa", "tokenization"
        }
        title_lower = title.lower()
        matched = [kw for kw in keywords if kw in title_lower]
        
        # Confidence base
        confidence = 0.25  # baseline for Cointelegraph
        if matched:
            confidence += min(len(matched) * 0.05, 0.15)
        if any(w in title_lower for w in ["bitcoin", "btc", "ethereum", "eth"]):
            confidence += 0.1
        if any(w in title_lower for w in ["regulation", "sec", "etf", "fed"]):
            confidence += 0.1
        
        # Lane routing
        if confidence >= 0.45:
            lane = "medium_signal"
            action = "append_with_review_flag"
        elif confidence >= 0.35:
            lane = "low_signal"
            action = "queue"
        else:
            lane = "low_signal"
            action = "archive_only"
        
        # Parse timestamp
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        if pub_date:
            try:
                from email.utils import parsedate_to_datetime
                ts = parsedate_to_datetime(pub_date).strftime("%Y-%m-%dT%H:%M:%S")
            except:
                pass
        
        event = {
            "source_id": "cointelegraph",
            "event_type": "market_news",
            "timestamp": ts,
            "lane": lane,
            "action": action,
            "confidence": round(confidence, 2),
            "headline": title,
            "payload": {
                "headline": title,
                "url": link,
                "description": description[:500] if description else "",
                "keywords": matched
            },
            "provenance_hash": content_hash
        }
        items.append(event)
    
    # Output as JSONL
    for ev in items:
        print(json.dumps(ev))
    
    print(f"[cointelegraph] {len(items)} articles ingested", file=sys.stderr)
    
except Exception as e:
    print(f"[cointelegraph] ERROR: {e}", file=sys.stderr)
    print(json.dumps({
        "source_id": "cointelegraph",
        "event_type": "ingestion_error",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "lane": "low_signal",
        "action": "log",
        "confidence": 0.0,
        "headline": f"Cointelegraph RSS failed: {e}",
        "provenance_hash": f"error:{hashlib.sha256(str(e).encode()).hexdigest()[:16]}"
    }))
    sys.exit(1)
