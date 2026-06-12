#!/usr/bin/env python3
"""
Sage — content-based source detector for Telegram HTML exports.

Reads DuckDB events with unknown source, re-parses the original HTML files,
extracts @handle mentions, forwarded-from headers, and channel descriptions.
Updates source_id in events table.

Perplexity Round 5 patterns:
  - <title> tag → channel name
  - "Forwarded from @handle" → source
  - @handle in message body → source candidate
  - t.me/channel URL → source candidate
  - Channel description keyword match

Usage: python3 sage.py [--dry-run] [--reprocess]
"""
import json, os, re, sys
from datetime import datetime, timezone
from pathlib import Path

KESTREL = "/home/synczus/kestrel"
DB = os.path.join(KESTREL, "signals.duckdb")

# Known channel names from our source list
KNOWN_SOURCES = {
    "whalealert": "whale-alert", "whale_alert": "whale-alert", "WhaleAlert": "whale-alert",
    "disclosetv": "disclosetv", "disclose_tv": "disclosetv", "DiscloseTV": "disclosetv",
    "realDonaldTrump": "realDonaldTrump",
    "gemhunterrrs": "gemhunterrrs", "GEMHUNTERRRS": "gemhunterrrs",
    "cryptoquant": "cryptoquant-com", "CryptoQuant": "cryptoquant-com",
    "wublockchain": "wublockchain", "WuBlockchain": "wublockchain",
    "unfolded": "unfolded", "Unfolded": "unfolded",
    "diamondcrab": "diamondcrab", "DiamondCrab": "diamondcrab",
    "cryptogoodreads": "cryptogoodreads", "CryptoGoodreads": "cryptogoodreads",
    "thebabylonian": "thebabylonian", "TheBabylonian": "thebabylonian",
    "qcpcapital": "qcpcapital", "QCPCapital": "qcpcapital",
    "messaritg": "messaritg", "MessariTG": "messaritg",
    "theblocktg": "theblocktg", "TheBlockTG": "theblocktg",
    "glassnode": "glassnode", "Glassnode": "glassnode",
    "binancekillers": "binance-killers", "BinanceKillers": "binance-killers",
    "londoncryptoclub": "londoncryptoclub", "LondonCryptoClub": "londoncryptoclub",
    "investanswers": "investanswers", "InvestAnswers": "investanswers",
    "a16zcrypto": "a16z-crypto", "a16z_crypto": "a16z-crypto",
    "cointelegraph": "cointelegraph", "Cointelegraph": "cointelegraph",
    "coinstack": "coinstack", "Coinstack": "coinstack",
    "thetechbuzz": "the-tech-buzz", "the_tech_buzz": "the-tech-buzz", "TheTechBuzz": "the-tech-buzz",
    "bankless": "bankless", "Bankless": "bankless",
    "milkroad": "milk-road", "milk_road": "milk-road", "MilkRoad": "milk-road",
    "theneuron": "the-neuron", "the_neuron": "the-neuron", "TheNeuron": "the-neuron",
    "mindstream": "mindstream", "Mindstream": "mindstream",
    "defillama": "defillama", "DeFiLlama": "defillama",
    "coinstats": "coinstats", "CoinStats": "coinstats",
    "finnhub": "finnhub", "Finnhub": "finnhub",
    "awesome_tech_rss": "awesome-tech-rss", "awesometechrss": "awesome-tech-rss",
    "cryptocurrency_cv": "cryptocurrency-cv",
    "crypto_garden": "crypto-garden",
    "cryptoninjas": "crypto-ninjas",
    "cryptoninjas_trading": "crypto-ninjas",
}

def log(s):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[sage {ts}] {s}", flush=True)

def normalize_handle(raw: str) -> str | None:
    """Convert @WhaleAlert or @whale_alert or @whalealert → canonical source_id.
    Returns None if handle doesn't match any known source."""
    clean = raw.replace("@", "").strip()
    
    # Direct lookup first
    canonical = KNOWN_SOURCES.get(clean) or KNOWN_SOURCES.get(clean.lower())
    if canonical:
        return canonical
    
    # Try normalized variants
    normalized = clean.lower().replace("_", "").replace("-", "")
    canonical = KNOWN_SOURCES.get(normalized)
    if canonical:
        return canonical
    
    # Too short (3-4 chars) is almost certainly noise unless it's in our known list
    if len(clean) < 5:
        return None
    
    return None

def extract_title_source(html: str) -> str | None:
    """Extract Telegram channel name from <title> tag."""
    m = re.search(r'<title>\s*(?:Telegram:\s*)?@?([^<]+?)\s*</title>', html, re.IGNORECASE)
    if m:
        name = m.group(1).strip()
        if name:
            result = normalize_handle(name)
            if result:
                return result
            # Title might have channel name that isn't a @handle — check against known names
            name_lower = name.lower().replace(" ", "")
            if name_lower in KNOWN_SOURCES:
                return KNOWN_SOURCES[name_lower]
    return None

def extract_forwarded_from(text: str) -> str | None:
    """Extract @handle from 'Forwarded from @channel' patterns."""
    m = re.search(r'(?:Forwarded\s+from|via)\s+@?([A-Za-z0-9_]{3,40})', text, re.IGNORECASE)
    if m:
        return normalize_handle(m.group(1))
    return None

def extract_handle_from_text(text: str) -> str | None:
    """Extract @handle mentions that match known sources."""
    handles = re.findall(r'(?<!\w)@([A-Za-z0-9_]{3,40})(?:\b|(?=[^A-Za-z0-9_]))', text)
    for h in handles:
        canonical = normalize_handle(h)
        if canonical != f"@{h}":  # It matched a known source
            return canonical
    return None

def extract_telegram_url(text: str) -> str | None:
    """Extract channel name from t.me/ChannelName URL."""
    m = re.search(r'https?://t\.me/([A-Za-z0-9_]{3,40})\b', text)
    if m:
        return normalize_handle(m.group(1))
    return None

def detect_source_from_html(html: str, first_few_messages: list[str]) -> str | None:
    """Try all detection strategies, return best match."""
    # 1. Title tag (most reliable)
    src = extract_title_source(html)
    if src and not src.startswith("@"):
        return src
    
    # 2. First few messages for forwarded-from headers
    for msg in first_few_messages[:10]:
        src = extract_forwarded_from(msg)
        if src:
            return src
    
    # 3. Known handles in message bodies
    for msg in first_few_messages:
        src = extract_handle_from_text(msg)
        if src:
            return src
    
    # 4. t.me URLs
    for msg in first_few_messages:
        src = extract_telegram_url(msg)
        if src:
            return src
    
    # 5. Content-based signatures (fallback)
    full_text = " ".join(first_few_messages[:20]).lower()
    
    # Whale Alert: whale-alert.io, official whale alert channel
    if "whale-alert.io" in full_text or ("whale alert" in full_text and "official" in full_text):
        return "whale-alert"
    
    # Binance Killers: SIGNAL ID format with ENTRY/STOP LOSS or leverage/target patterns
    if ("signal id:" in full_text and "entry :" in full_text and ("stop loss" in full_text or "leverage" in full_text)):
        return "binance-killers"
    if "binance analysis:" in full_text and "cannot be forwarded" in full_text:
        return "binance-killers"
    if "leverage:50x" in full_text and "t-p targets" in full_text and "stop-loss:" in full_text:
        return "binance-killers"
    
    # Crypto Garden: airdrop + giveaway + casino + promo mix
    airdrop_keywords = ["new airdrop", "pepe pharaoh", "abex finance", "rollman mining", "cryptoplay", "giveaway", "eth + wl"]
    if sum(1 for kw in airdrop_keywords if kw in full_text) >= 2:
        return "crypto-garden"
    # Also detect @handle-heavy promo content with airdrop/giveaway patterns
    if "airdrop" in full_text and ("giveaway" in full_text or "eth" in full_text) and len(first_few_messages) >= 3:
        return "crypto-garden"
    
    # GemHunter: 50x leverage signals with Binance Futures
    if "binance futures" in full_text and "leverage:" in full_text and "profit:" in full_text and "%" in full_text:
        return "gemhunterrrs"
    
    # CryptoNinjas: Binance Futures 50x leverage with specific from_name pattern
    # The HTML has from_name 'CryptoNinjas Trading' in the page header
    if "cryptoninjas" in full_text:
        return "crypto-ninjas"
    
    # Binance Futures generic signals: 50x leverage + entry price + stop-loss
    if "binance futures" in full_text and "leverage:50x" in full_text and "entire price" in full_text:
        if "t-p targets" in full_text and "stop-loss" in full_text:
            return "crypto-ninjas"
    
    # Hermes bot chat: bot infrastructure logs
    if "home channel" in full_text and "hermes" in full_text and ("sethome" in full_text or "cross-platform" in full_text):
        return "hermes-bot-chat"
    
    return None

def run(dry_run: bool = False):
    try:
        import duckdb
        from bs4 import BeautifulSoup
    except ImportError as e:
        log(f"Missing dep: {e}")
        return 1
    
    con = duckdb.connect(DB)
    
    # Get all events with unknown source_id
    unknown = con.execute("""
        SELECT row_id, provenance_source_url, payload_body, payload_headline
        FROM events
        WHERE source_id = 'unknown-telegram-export'
    """).fetchall()
    
    log(f"Found {len(unknown)} events with unknown source_id")
    
    if not unknown:
        log("No unknown events to fix")
        return 0
    
    # Group by file path for efficiency
    by_file: dict[str, list] = {}
    for row_id, url, body, headline in unknown:
        if url not in by_file:
            by_file[url] = []
        by_file[url].append((row_id, body, headline))
    
    log(f"Across {len(by_file)} unique HTML files")
    
    updates = 0
    resolved_hits = {}
    
    for file_path, events in by_file.items():
        if not os.path.exists(file_path):
            log(f"File not found (skipped): {file_path}")
            continue
        
        try:
            with open(file_path, 'r', errors='ignore') as f:
                html = f.read()
        except Exception as e:
            log(f"Read error: {file_path}: {e}")
            continue
        
        # Parse HTML to get message texts for detection
        soup = BeautifulSoup(html, 'lxml')
        messages = []
        for node in soup.select('div.message div.text'):
            messages.append(node.get_text(' ', strip=True))
        
        # Use first few messages for detection
        first_msgs = messages[:20] if messages else [e[1][:500] for e in events[:3]]
        if not first_msgs:
            first_msgs = [""]
        
        source_id = detect_source_from_html(html, first_msgs)
        
        if source_id:
            resolved_hits[file_path] = source_id
            log(f"  {os.path.basename(file_path)} → {source_id} ({len(events)} events)")
            
            if not dry_run:
                row_ids = [e[0] for e in events]
                # Batch update
                con.executemany("""
                    UPDATE events SET source_id = ? WHERE row_id = ?
                """, [(source_id, rid) for rid in row_ids])
                updates += len(row_ids)
        else:
            log(f"  {os.path.basename(file_path)} → UNRESOLVED ({len(events)} events)")
    
    # Summary
    found = len(resolved_hits)
    total_files = len(by_file)
    log(f"Resolved {found}/{total_files} files ({updates}/{len(unknown)} events)")
    if found < total_files:
        unresolved = [os.path.basename(f) for f in by_file if f not in resolved_hits]
        log(f"Unresolved files: {unresolved}")
    
    # Re-score affected events
    if updates > 0 and not dry_run:
        log("Running post-ingest scorer to re-score updated events...")
        import subprocess
        subprocess.run([sys.executable, os.path.join(KESTREL, "scripts/ingestion", "post-ingest-scorer.py")])
    
    con.close()
    return 0

if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    sys.exit(run(dry_run=dry))