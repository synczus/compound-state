#!/usr/bin/env python3
# Run: source /home/synczus/kestrel/venv/bin/activate && python3 trade-extractor.py
"""
trade-extractor.py — Extract structured trade setups from raw signal text.

Scans the signals table for raw Telegram signals containing trade language
(LONG/SHORT, entry prices, TP levels, SL levels) and writes structured
trade_setups entries with: asset, direction, entry_price, TP1-3, SL,
risk_reward_ratio, rationale.

Runs as a systemd timer every 15 min, or on-demand for backfill.

Usage:
  python3 trade-extractor.py                    # Scan new signals only
  python3 trade-extractor.py --backfill          # Scan ALL unprocessed signals  
  python3 trade-extractor.py --dry-run           # Show what would be extracted
"""

import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone

try:
    import duckdb
except ImportError:
    print("duckdb required: pip install duckdb", file=sys.stderr)
    sys.exit(1)

DB_PATH = "/home/synczus/kestrel/signals.duckdb"

# Known crypto asset symbols to match
ASSETS = {
    'BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'DOT', 'LINK', 'AVAX', 'MATIC',
    'UNI', 'ATOM', 'ALGO', 'FIL', 'NEAR', 'APT', 'SUI', 'ARB', 'OP', 'INJ',
    'PEPE', 'BONK', 'WIF', 'FLOKI', 'SHIB', 'AAVE', 'MKR', 'CRV', 'COMP',
    'LTC', 'BCH', 'ETC', 'XLM', 'TRX', 'VET', 'EGLD', 'EOS', 'ICP', 'FTM',
    'SAND', 'MANA', 'AXS', 'BNB', 'CAKE', 'RUNE', 'THETA', 'KCS', 'HT', 'OKB',
    'TIA', 'SEI', 'STRK', 'DYM', 'PIXEL', 'PORTAL', 'W', 'ENA', 'ETHFI',
    'AI', 'AGIX', 'FET', 'OCEAN', 'RNDR', 'GRT', 'TAO'
}

# Trading direction keywords
DIRECTION_PATTERNS = [
    (r'\bLONG\b', 'LONG'),
    (r'\bBUY\b', 'LONG'),
    (r'\bBULLISH\b', 'LONG'),
    (r'\bSHORT\b', 'SHORT'),
    (r'\bSELL\b', 'SHORT'),
    (r'\bBEARISH\b', 'SHORT'),
]

# Price extraction patterns
ENTRY_PATTERNS_V2 = [
    # ENTRY: OTE first (Optimal Entry): "ENTRY: 190 - 210OTE: 202.83"
    r'OTE:\s*\$?([\d,]+\.?\d*)',
    # ENTRY range: "ENTRY: $32 - $33"
    r'ENTRY:\s*\$?([\d,]+\.?\d*)\s*-\s*\$?([\d,]+\.?\d*)',
    # ENTRY single: "ENTRY: 875"
    r'ENTRY:\s*\$?([\d,]+\.?\d*)',
    # Generic fallback
    r'(?:entry|enter|price|buy)[:\s]*\$?([\d,]+\.?\d*)',
    r'(?:at|around)[:\s]*\$?([\d,]+\.?\d*)',
]

TP_PATTERNS_V2 = [
    # Short Term Target 1: 43,700
    r'Short\s*Term[\s:]*(?:Target\s*\d*[\s:]*)?\$?([\d,]+\.?\d*)',
    # Target 1: 4900 / Target 2: 5400
    r'Target\s*\d+[\s:]*\$?([\d,]+\.?\d*)',
    # TARGETSShort Term: 980 - 1050 - 1120
    r'TARGETSShort\s*Term[\s:]*\$?([\d,]+\.?\d*)',
    # Generic: TP / take profit / target
    r'(?:TP|target|take[\s-]*profit)[:\s#]*(\d*)[:\s]*\$?([\d,]+\.?\d*)',
    # Arrow format (→ price)
    r'(?:→|➡️|➖>)[:\s]*\$?([\d,]+\.?\d*)',
]

SL_PATTERNS_V2 = [
    # STOP LOSS with optional "Below": "STOP LOSS: Below 163.8"
    r'STOP\s*LOSS[\s:]*(?:Below\s*)?\$?([\d,]+\.?\d*)',
    r'(?:SL|stop[\s-]*loss|stop)[:\s]*\$?([\d,]+\.?\d*)',
    r'STOP[\s:]*\$?([\d,]+\.?\d*)',
]

LEVERAGE_PATTERNS = [
    r'(\d+\.?\d*)[xX]',
    r'(\d+\.?\d*)\s*[xX]',
]


def clean_price(price_str):
    """Convert a price string like '1,661.43' to float."""
    try:
        return float(price_str.replace(',', '').strip())
    except (ValueError, AttributeError):
        return None


def extract_asset(text, symbols):
    """Extract the traded asset from text or symbols array."""
    # First check the symbols column
    if symbols and isinstance(symbols, list):
        for sym in symbols:
            if sym.upper() in ASSETS:
                return sym.upper()
    
    # Search text for known assets
    for asset in sorted(ASSETS, key=len, reverse=True):
        if re.search(r'\b' + asset + r'\b', text.upper()):
            return asset
    
    # Match USD pairs
    m = re.search(r'\$([A-Z]{2,10})', text)
    if m:
        return m.group(1)
    
    return None


def extract_direction(text):
    """Extract LONG/SHORT direction."""
    for pattern, direction in DIRECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return direction
    return None


def extract_prices(text):
    """Extract entry, TP levels, and SL from signal text."""
    result = {
        'entry_price': None,
        'take_profit_1': None,
        'take_profit_2': None,
        'take_profit_3': None,
        'stop_loss': None,
        'leverage': None,
        'risk_reward_ratio': None,
    }
    
    # --- ENTRY PRICE (v2) ---
    # 1. OTE (Optimal Trade Entry): "OTE: 202.83"
    ote_match = re.search(r'OTE:\s*\$?([\d,]+\.?\d*)', text, re.IGNORECASE)
    if ote_match:
        result['entry_price'] = clean_price(ote_match.group(1))
    
    # 2. ENTRY range: "ENTRY: $32 - $33" → midpoint
    if not result['entry_price']:
        range_match = re.search(r'ENTRY:\s*\$?([\d,]+\.?\d*)\s*-\s*\$?([\d,]+\.?\d*)', text, re.IGNORECASE)
        if range_match:
            lo = clean_price(range_match.group(1))
            hi = clean_price(range_match.group(2))
            if lo and hi:
                result['entry_price'] = round((lo + hi) / 2, 2)
    
    # 3. ENTRY single: "ENTRY: 875"
    if not result['entry_price']:
        single_match = re.search(r'ENTRY:\s*\$?([\d,]+\.?\d*)', text, re.IGNORECASE)
        if single_match:
            result['entry_price'] = clean_price(single_match.group(1))
    
    # 4. Generic fallback
    if not result['entry_price']:
        generic_match = re.search(r'(?:entry|enter|price|buy)[:\s]*\$?([\d,]+\.?\d*)', text, re.IGNORECASE)
        if generic_match:
            result['entry_price'] = clean_price(generic_match.group(1))
    
    # --- TAKE PROFIT LEVELS (v2) ---
    tp_matches = []
    
    # 1. Short Term Target 1: X,XXX - multi-price format
    short_term = re.findall(r'Short\s*Term[\s:]*(?:Target\s*\d*[\s:]*)?\$?([\d,]+(?:\.\d+)?)', text, re.IGNORECASE)
    for p in short_term:
        price = clean_price(p)
        if price and price not in tp_matches:
            tp_matches.append(price)
    
    # 2. If no Short Term found, try numbered targets
    if not tp_matches:
        targets = re.findall(r'(?:Short\s*Term\s*)?Target\s*\d+[\s:]*\$?([\d,]+(?:\.\d+)?)', text, re.IGNORECASE)
        for p in targets:
            price = clean_price(p)
            if price and price not in tp_matches:
                tp_matches.append(price)
    
    # 3. TARGETSShort Term format
    if not tp_matches:
        inline = re.findall(r'TARGETSShort\s*Term[\s:]*\$?([\d,]+(?:\.\d+)?)', text, re.IGNORECASE)
        for p in inline:
            price = clean_price(p)
            if price and price not in tp_matches:
                tp_matches.append(price)
    
    # Sort: for LONG ascending (lower first), for SHORT descending (higher first = closer)
    direction = extract_direction(text)
    if tp_matches:
        if direction == 'SHORT':
            tp_matches.sort()
        else:
            tp_matches.sort()
    
    for i, tp in enumerate(tp_matches[:3]):
        result[f'take_profit_{i+1}'] = tp
    
    # --- STOP LOSS (v2) ---
    sl_match = re.search(r'STOP\s*LOSS[\s:]*(?:Below\s*)?\$?([\d,]+\.?\d*)', text, re.IGNORECASE)
    if not sl_match:
        sl_match = re.search(r'(?:SL|stop[\s-]*loss|stop)[:\s]*\$?([\d,]+\.?\d*)', text, re.IGNORECASE)
    if not sl_match:
        sl_match = re.search(r'STOP[\s:]*\$?([\d,]+\.?\d*)', text, re.IGNORECASE)
    if sl_match:
        result['stop_loss'] = clean_price(sl_match.group(1))
    
    # --- LEVERAGE ---
    for pattern in LEVERAGE_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                result['leverage'] = float(m.group(1))
            except ValueError:
                pass
            break
    
    # --- R:R CALCULATION ---
    entry = result['entry_price']
    tp1 = result['take_profit_1']
    sl = result['stop_loss']
    
    if entry and tp1 and sl:
        if direction == 'SHORT':
            result['risk_reward_ratio'] = round(abs(entry - tp1) / abs(entry - sl), 2)
        else:
            result['risk_reward_ratio'] = round(abs(tp1 - entry) / abs(entry - sl), 2)
    
    return result


def build_rationale(text, prices, direction, asset):
    """Build a concise rationale from extracted data."""
    parts = []
    if asset:
        parts.append(f"{asset}")
    if direction:
        parts.append(f"{direction}")
    if prices.get('entry_price'):
        parts.append(f"entry ${prices['entry_price']}")
    if prices.get('take_profit_1'):
        parts.append(f"TP1 ${prices['take_profit_1']}")
    if prices.get('stop_loss'):
        parts.append(f"SL ${prices['stop_loss']}")
    if prices.get('leverage'):
        parts.append(f"{prices['leverage']}x")
    
    return ' | '.join(parts) if parts else "Raw signal — review manually"


def process_signals(backfill=False, dry_run=False):
    """Main entry point: scan signals table and extract trade setups."""
    con = duckdb.connect(DB_PATH)
    
    # Get the watermark of last processed signal (by ingested_at)
    if not backfill:
        last_ts = con.execute("""
            SELECT MAX(s.ingested_at)
            FROM signals s
            WHERE s.signal_id IN (SELECT signal_id FROM trade_setups WHERE signal_id IS NOT NULL)
        """).fetchone()[0]
        last_id = 1 if last_ts else 0
    else:
        last_id = 0
    
    # Fetch unprocessed signals with trading language
    query = """
        SELECT signal_id, body_text, symbols, confidence, source_id, event_type, ingested_at
        FROM signals
        WHERE (body_text LIKE '%ENTRY:%' OR body_text LIKE '%Direction: LONG%' OR body_text LIKE '%Direction: SHORT%')
          AND body_text NOT LIKE '%✅%'
          AND body_text NOT LIKE '%Profit%'
    """
    if not backfill and last_ts:
        query += f" AND ingested_at > '{last_ts}'::TIMESTAMP"
    
    query += " ORDER BY ingested_at DESC LIMIT 200"
    
    signals = con.execute(query).fetchall()
    
    if not signals:
        print(f"[trade-extractor] No new signals to process")
        con.close()
        return 0
    
    extracted = 0
    new_setups = []
    
    for sig in signals:
        sid, body, symbols, confidence, source_id, event_type, ingested = sig
        
        if not body or len(str(body).strip()) < 20:
            continue
        
        text = str(body)
        
        # Extract structured data
        asset = extract_asset(text, symbols)
        direction = extract_direction(text)
        prices = extract_prices(text)
        
        # Skip if no actionable data found
        if not asset and not direction and not prices.get('entry_price'):
            continue
        
        # Build rationale
        rationale = build_rationale(text, prices, direction, asset)
        
        # Ensure we have confidence
        conf_str = 'HIGH' if confidence and confidence >= 0.25 else 'MEDIUM' if confidence and confidence >= 0.15 else 'LOW'
        
        setup = {
            'setup_id': str(uuid.uuid4()),
            'asset': asset or 'UNKNOWN',
            'direction': direction or 'NEUTRAL',
            'entry_price': prices['entry_price'] or -1.0,
            'current_price': prices['entry_price'] or -1.0,
            'take_profit_1': prices['take_profit_1'] or -1.0,
            'take_profit_2': prices['take_profit_2'] or -1.0,
            'take_profit_3': prices['take_profit_3'] or -1.0,
            'stop_loss': prices['stop_loss'] or -1.0,
            'risk_reward_ratio': prices['risk_reward_ratio'] or -1.0,
            'position_size_usd': -1.0,
            'edge_score': confidence or 0.0,
            'source_prior': confidence or 0.0,
            'confidence': conf_str,
            'source_id': source_id or 'unknown',
            'event_type': event_type or 'trade_signal',
            'rationale': rationale,
            'signal_id': sid,
            'budget_remaining': 0.0,
            'status': 'pending',
            'generated_at': datetime.now(timezone.utc),
        }
        
        new_setups.append(setup)
        extracted += 1
    
    # Skip signals that already have setups (dedup)
    if new_setups and not dry_run:
        existing = set()
        try:
            existing = set(row[0] for row in con.execute(
                "SELECT signal_id FROM trade_setups WHERE signal_id IS NOT NULL"
            ).fetchall())
        except:
            pass
        new_setups = [s for s in new_setups if s['signal_id'] not in existing]
        if not new_setups:
            print(f"[trade-extractor] All {len(existing)} signals already have setups — nothing new")
            con.close()
            return 0
    
    # Write to DuckDB
    if new_setups and not dry_run:
        con.execute("BEGIN TRANSACTION")
        for s in new_setups:
            con.execute("""
                INSERT INTO trade_setups 
                (setup_id, asset, direction, entry_price, current_price, 
                 take_profit_1, take_profit_2, take_profit_3, stop_loss,
                 risk_reward_ratio, position_size_usd, edge_score, source_prior,
                 confidence, source_id, event_type, rationale, signal_id,
                 budget_remaining, status, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                s['setup_id'], s['asset'], s['direction'], s['entry_price'], s['current_price'],
                s['take_profit_1'], s['take_profit_2'], s['take_profit_3'], s['stop_loss'],
                s['risk_reward_ratio'], s['position_size_usd'], s['edge_score'], s['source_prior'],
                s['confidence'], s['source_id'], s['event_type'], s['rationale'], s['signal_id'],
                s['budget_remaining'], s['status'], s['generated_at']
            ])
        con.execute("COMMIT")
    
    # Summary
    action = "DRY RUN" if dry_run else "INSERTED"
    print(f"[trade-extractor] Scanned {len(signals)} signals, {action} {extracted} trade setups")
    
    if new_setups:
        print(f"\nTop extracted setups:")
        for s in new_setups[:5]:
            entry = f"${s['entry_price']}" if s['entry_price'] > 0 else "N/A"
            tp1 = f"${s['take_profit_1']}" if s['take_profit_1'] > 0 else "N/A"
            sl = f"${s['stop_loss']}" if s['stop_loss'] > 0 else "N/A"
            rr = f"R:R {s['risk_reward_ratio']}" if s['risk_reward_ratio'] > 0 else ""
            print(f"  {s['asset']} {s['direction']} → entry={entry} TP1={tp1} SL={sl} {rr} [{s['confidence']}]")
    
    con.close()
    return extracted


if __name__ == "__main__":
    backfill = '--backfill' in sys.argv
    dry_run = '--dry-run' in sys.argv
    
    count = process_signals(backfill=backfill, dry_run=dry_run)
    
    if count > 0:
        print(f"\n✅ {count} trade setups extracted")
    else:
        print(f"\n📭 No trade data found in signals — waiting for new data")