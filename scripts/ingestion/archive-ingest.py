#!/usr/bin/env python3
"""
Archive Batch Processor — ingests all 15 Telegram export files from media/inbound/
Perplexity's build order Step 1: highest leverage because exports are sitting on disk.

Processes: scans inbound dir, detects new HTML exports, extracts messages,
normalizes to event schema, SHA256 dedup, bulk-inserts into DuckDB.
Idempotent: marks processed files in a manifest table.
"""
import json, os, re, sys, hashlib, html
from datetime import datetime, timezone
from pathlib import Path

KESTREL = "/home/synczus/kestrel"
STAGING = os.path.join(KESTREL, "ingestion", "staging")
INBOUND = os.path.expanduser("~/.openclaw/media/inbound")
CONFIG = os.path.join(KESTREL, "manifests", "coordination.yaml")

# NEW: Write to JSONL staging file instead of direct DuckDB
# The post-ingest-scorer reads staging files and bulk-inserts into DuckDB
STAGING_FILE = os.path.join(STAGING, f"events_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.jsonl")

# Source detection by filename/pattern
SOURCE_DETECT = [
    (r"whale.?alert", "whale-alert"),
    (r"disclose.?tv|disclosetv", "disclosetv"),
    (r"coin.?telegraph|cointelegraph", "cointelegraph"),
    (r"crypto.?garden|cryptogarden", "crypto-garden"),
    (r"tyler.?trades|tylertrades", "tyler-trades"),
    (r"gem.?hunter|gemhunter", "gemhunter"),
    (r"binance.?kill|bination-killer", "binance-killers"),
    (r"the.?econgram|econgram", "the-econgram"),
    (r"kobeissi", "kobeissi-letter"),
    (r"unusual.?whales|unusualwhales", "unusual-whales"),
    (r"crypto.?goodreads|cryptogoodreads", "crypto-goodreads"),
    (r"diamond.?crab|diamondcrab", "diamondcrab-crypto"),
    (r"babylonian", "the-babylonian"),
    (r"the.?block|theblock", "the-block"),
    (r"startups?", "startups"),
    (r"tech.?crunch|techcrunch", "techcrunch"),
    (r"a16z", "a16z-crypto"),
    (r"milk.?road|milkroad", "milk-road"),
    (r"bankless", "bankless"),
]

# Common crypto symbols for asset detection
CRYPTO_SYMBOLS = re.compile(
    r"\b(BTC|ETH|SOL|XRP|ADA|DOT|AVAX|LINK|MATIC|UNI|ATOM|LTC|BCH|XLM|DOGE|SHIB|FTM|NEAR|ALGO|AAVE|APE|FIL|ICP|EOS|XTZ|TRX|VET|SAND|MANA|GALA|AXS|CRV|SUSHI|COMP|MKR|YFI|SNX|BNB|USDT|USDC|DAI|TUSD)\b",
    re.IGNORECASE
)

def log(s):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[archive {ts}] {s}")

def detect_source(filename):
    """Detect source_id from filename."""
    fname = filename.lower()
    for pattern, source_id in SOURCE_DETECT:
        if re.search(pattern, fname):
            return source_id
    return "unknown-telegram-export"

def extract_messages(html_path):
    """Extract messages from a Telegram HTML export file."""
    try:
        from bs4 import BeautifulSoup
    except:
        log("Need beautifulsoup4: pip3 install beautifulsoup4")
        return []
    
    messages = []
    try:
        with open(html_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        log(f"Cannot read {html_path}: {e}")
        return []
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find all message divs
    msg_divs = soup.find_all('div', class_='message')
    
    # If no message divs, try simpler parsing (raw text lines)
    if not msg_divs:
        # Extract text between timestamps
        body = soup.get_text()
        lines = [l.strip() for l in body.split('\n') if l.strip()]
        if len(lines) > 5:
            # Treat as single large message
            return [{
                "text": '\n'.join(lines[:500]),
                "timestamp": None,
                "message_id": hashlib.sha256(str(content[:500]).encode()).hexdigest()[:16]
            }]
        return []
    
    for div in msg_divs:
        try:
            # Extract timestamp
            date_div = div.find('div', class_='date')
            timestamp = date_div.get_text(strip=True) if date_div else None
            
            # Extract text
            text_div = div.find('div', class_='text')
            text = text_div.get_text(strip=True) if text_div else None
            
            # Extract message ID
            msg_id = div.get('id', '').replace('message', '').strip()
            
            if text and len(text) > 5:
                # Detect symbols in text
                symbols = list(set(m.group().upper() for m in CRYPTO_SYMBOLS.finditer(text)))
                
                messages.append({
                    "text": text,
                    "timestamp": timestamp,
                    "message_id": msg_id or hashlib.sha256(text.encode()).hexdigest()[:12],
                    "symbols": symbols
                })
        except:
            continue
    
    return messages

def parse_timestamp(ts_str):
    """Parse Telegram timestamp format to ISO."""
    if not ts_str:
        return None
    # Try common formats
    for fmt in [
        "%Y-%m-%d %H:%M:%S",
        "%d.%m.%Y %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%d %b %Y %H:%M:%S",
        "%b %d, %Y %H:%M:%S"
    ]:
        try:
            return datetime.strptime(ts_str.strip(), fmt).isoformat()
        except:
            continue
    return None

def compute_dedup_key(text, source_id):
    """SHA256 dedup key: text hash + source_id."""
    return hashlib.sha256(f"{text}_{source_id}".encode()).hexdigest()

def classify_event(text):
    """Basic event classification from text content."""
    text_lower = text.lower()
    
    # Whale transaction patterns
    if re.search(r'\b\d+[,]?\d*\s*(BTC|ETH|USDT|USDC)\b', text, re.IGNORECASE):
        return "whale_transfer"
    
    # Price moves
    if any(w in text_lower for w in ["price", "surge", "plunge", "rally", "dump", "pump", "ATH"]):
        return "price_event"
    
    # Regulatory
    if any(w in text_lower for w in ["SEC", "regulation", "ban", "legal", "lawsuit", "court", "CFTC"]):
        return "regulatory_event"
    
    # Geopolitical
    if any(w in text_lower for w in ["CENTCOM", "sanction", "war", "conflict", "military", "troop", 
                                      "attack", "strike", "missile", "drone", "NATO"]):
        return "geopolitical_event"
    
    # Funding/Raises
    if any(w in text_lower for w in ["raised", "funding", "series", "valuation", "investment"]):
        return "funding_event"
    
    return "general_news"

def extract_telegram_source(text):
    """Try to detect original source from message text."""
    # Common Telegram source formats
    m = re.search(r'@(\w+)', text)
    if m:
        return f"telegram-@{m.group(1)}"
    return None

def run():
    import yaml
    
    try:
        from bs4 import BeautifulSoup
    except:
        log("Missing beautifulsoup4. Install: pip3 install beautifulsoup4")
        return 1
    
    # Load config
    config = yaml.safe_load(open(CONFIG))
    baselines = config["signal_ingestion"]["source_baselines"]
    generic_bl = baselines.get("generic-news", {"baseline": 0.30})
    
    # Load manifest from local JSON (avoids DuckDB concurrent write risk)
    manifest_path = os.path.join(STAGING, "archive_manifest.json")
    manifest = {"files": {}}
    if os.path.exists(manifest_path):
        try:
            manifest = json.load(open(manifest_path))
        except:
            manifest = {"files": {}}
    processed = set(manifest.get("files", {}).keys())
    
    # Get next row_id from manifest
    max_row = int(manifest.get("last_row_id", 0))
    
    # Scan inbound dir
    inbound_path = Path(INBOUND)
    if not inbound_path.exists():
        log(f"Inbound dir not found: {INBOUND}")
        return 1
    
    html_files = sorted([f for f in inbound_path.glob("*.html") if f.is_file()])
    log(f"Found {len(html_files)} HTML files in inbound/{len(processed)} already processed")
    
    total_new = 0
    batch_events = []
    
    for fp in html_files:
        abs_path = str(fp.resolve())
        
        # Skip already processed
        if abs_path in processed:
            continue
        
        # Detect source
        source_id = detect_source(fp.name)
        
        # Read and hash file
        file_hash = hashlib.sha256(open(abs_path, 'rb').read()).hexdigest()
        
        # Extract messages
        messages = extract_messages(abs_path)
        
        if not messages:
            log(f"No messages extracted from {fp.name}")
            continue
        
        msg_count = 0
        for msg in messages:
            text = msg.get("text", "")
            if not text:
                continue
            
            max_row += 1
            msg_count += 1
            
            # Compute dedup key
            dedup = compute_dedup_key(text[:200], source_id)
            
            # Parse timestamp
            ts = parse_timestamp(msg.get("timestamp", ""))
            if not ts:
                ts = datetime.now(timezone.utc).isoformat()
            
            # Classify
            event_type = classify_event(text)
            
            # Get baseline from config
            bl = baselines.get(source_id, generic_bl)
            
            # Detect symbols
            symbols = msg.get("symbols", [])
            
            # Detect Telegram source reference
            telegram_source = extract_telegram_source(text)
            
            batch_events.append({
                "source_id": telegram_source or source_id,
                "event_type": event_type,
                "timestamp": ts,
                "headline": text[:600],
                "body": text[:2000],
                "symbols": ",".join(symbols) if symbols else None,
                "provenance_url": abs_path,
                "provenance_hash": dedup[:32]
            })
        
        total_new += msg_count
        
        # Mark file as processed in local manifest
        manifest["files"][abs_path] = {
            "hash": file_hash,
            "source": source_id,
            "count": msg_count,
            "processed_at": datetime.now(timezone.utc).isoformat()
        }
        
        log(f"  {fp.name}: {msg_count} messages ({source_id})")
    
    # Write events to staging JSONL file (for scorer to consume)
    if batch_events:
        staging_path = os.path.join(STAGING, f"events_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.jsonl")
        os.makedirs(STAGING, exist_ok=True)
        with open(staging_path, 'w') as f:
            for evt in batch_events:
                f.write(json.dumps(evt) + '\n')
        
        # Update manifest with last row_id
        manifest["last_row_id"] = max_row
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        log(f"Wrote {len(batch_events)} events to {staging_path}")
    else:
        log("No new events to write")
    
    # Summary
    file_count = len([f for f in html_files if str(f.resolve()) not in processed])
    log(f"Processed {file_count} files, {total_new} new events")
    
    return 0 if total_new > 0 else 0
    
    # Scan inbound dir
    inbound_path = Path(INBOUND)
    if not inbound_path.exists():
        log(f"Inbound dir not found: {INBOUND}")
        return 1
    
    html_files = sorted([f for f in inbound_path.glob("*.html") if f.is_file()])
    log(f"Found {len(html_files)} HTML files in inbound/{len(processed)} already processed")
    
    total_new = 0
    batch_events = []
    
    for fp in html_files:
        abs_path = str(fp.resolve())
        
        # Skip already processed
        if abs_path in processed:
            continue
        
        # Detect source
        source_id = detect_source(fp.name)
        
        # Read and hash file
        file_hash = hashlib.sha256(open(abs_path, 'rb').read()).hexdigest()
        
        # Extract messages
        messages = extract_messages(abs_path)
        
        if not messages:
            log(f"No messages extracted from {fp.name}")
            continue
        
        msg_count = 0
        for msg in messages:
            text = msg.get("text", "")
            if not text:
                continue
            
            max_row += 1
            msg_count += 1
            
            # Compute dedup key
            dedup = compute_dedup_key(text[:200], source_id)
            
            # Parse timestamp
            ts = parse_timestamp(msg.get("timestamp", ""))
            if not ts:
                ts = datetime.now(timezone.utc).isoformat()
            
            # Classify
            event_type = classify_event(text)
            
            # Get baseline from config
            bl = baselines.get(source_id, generic_bl)
            baseline_score = bl.get("baseline", 0.30)
            
            # Detect symbols
            symbols = msg.get("symbols", [])
            
            # Detect Telegram source reference
            telegram_source = extract_telegram_source(text)
            
            batch_events.append((
                max_row,
                telegram_source or source_id,
                event_type,
                ts,
                text[:600],
                text[:2000],
                ",".join(symbols) if symbols else None,
                "queue",
                "archive_ingest",
                baseline_score,
                None,  # magnitude
                None,  # velocity
                abs_path,
                dedup[:32]
            ))
        
        total_new += msg_count
        
        # Mark file as processed in local manifest
        manifest["files"][abs_path] = {
            "hash": file_hash,
            "source": source_id,
            "count": msg_count,
            "processed_at": datetime.now(timezone.utc).isoformat()
        }
        
        log(f"  {fp.name}: {msg_count} messages ({source_id})")
    
    # Write events to staging JSONL file (for scorer to consume)
    if batch_events:
        staging_path = os.path.join(STAGING, f"events_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.jsonl")
        os.makedirs(STAGING, exist_ok=True)
        with open(staging_path, 'w') as f:
            for evt in batch_events:
                f.write(json.dumps(evt) + '\n')
        
        # Update manifest with last row_id
        manifest["last_row_id"] = max_row
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        log(f"Wrote {len(batch_events)} events to {os.path.relpath(staging_path)}")
    else:
        log("No new events to write")
    
    # Summary
    file_count = len([f for f in html_files if str(f.resolve()) not in processed])
    log(f"Processed {file_count} files, {total_new} new events")
    
    return 0 if total_new > 0 else 0

if __name__ == "__main__":
    sys.exit(run())