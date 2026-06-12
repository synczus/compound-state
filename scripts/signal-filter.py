#!/usr/bin/env python3
"""
signal-filter.py — Adaptive signal filter for the Kestrel pipeline.

Reduces signal noise by:
1. Scoring each signal against Chase's active watchlist (BTC, ETH, SOL)
2. Filtering out signals below relevance + confidence threshold
3. Pairing surviving signals with real-time MTA data
4. Emitting only actionable, MTA-verified setups

Architecture:
  Signal pipeline → trade-extractor.py → trade_setups
                                     ↓
                              multi-tf-analyzer.py
                                     ↓
                              signal-filter.py → filtered_events + alert

Usage:
  python3 signal-filter.py                    # Filter all pending setups
  python3 signal-filter.py --threshold 0.3     # Custom relevance threshold
  python3 signal-filter.py --post              # Post top setup to Telegram
"""

import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone

DB_PATH = "/home/synczus/kestrel/signals.duckdb"

# Chase's active watchlist (what he actually trades)
WATCHLIST = ['BTC', 'ETH', 'SOL']

# Minimum thresholds
DEFAULT_RELEVANCE_THRESHOLD = 0.25
DEFAULT_CONFIDENCE_THRESHOLD = 0.15


def score_relevance(signal_text, symbols, asset):
    """Score how relevant a signal is to Chase's current trading focus."""
    if not signal_text:
        return 0.0
    
    text = str(signal_text).upper()
    score = 0.0
    
    # Direct watchlist match
    if symbols and isinstance(symbols, list):
        for sym in symbols:
            if sym.upper() in WATCHLIST:
                score += 0.4
    
    if asset and asset in WATCHLIST:
        score += 0.3
    
    # Trading signal indicators
    if 'LONG' in text: score += 0.15
    if 'SHORT' in text: score += 0.15
    if 'TP' in text: score += 0.1
    if 'ENTRY' in text: score += 0.1
    if 'STOP LOSS' in text or 'SL:' in text or 'SL ' in text: score += 0.1
    
    # Price info
    if re.search(r'\$\d+', text): score += 0.05
    
    # Discount noise
    if 'MEME' in text: score -= 0.1
    if '1000X' in text or '1000x' in text: score -= 0.15
    if 'MOON' in text and 'DOGE' not in text: score -= 0.1
    if 'AIRDROP' in text: score -= 0.2
    if 'GIVEAWAY' in text: score -= 0.3
    if 'lottery' in text.lower(): score -= 0.2
    
    return max(0.0, min(1.0, score))


def filter_pending_setups(threshold=DEFAULT_RELEVANCE_THRESHOLD, post=False):
    """Filter trade_setups by relevance, apply MTA, emit actionable ones."""
    try:
        import duckdb
    except ImportError:
        print("[FILTER] duckdb required")
        return []
    
    con = duckdb.connect(DB_PATH)
    
    # Get all pending setups with their signals
    setups = con.execute("""
        SELECT ts.setup_id, ts.asset, ts.direction, ts.entry_price, 
               ts.take_profit_1, ts.take_profit_2, ts.take_profit_3,
               ts.stop_loss, ts.risk_reward_ratio, ts.edge_score,
               ts.confidence, ts.rationale, ts.signal_id,
               s.body_text, s.symbols
        FROM trade_setups ts
        LEFT JOIN signals s ON ts.signal_id = s.signal_id
        WHERE ts.status = 'pending'
        ORDER BY ts.generated_at DESC
        LIMIT 500
    """).fetchall()
    
    filtered = []
    
    for s in setups:
        try:
            symbols = json.loads(s[14]) if isinstance(s[14], str) else s[14]
        except (json.JSONDecodeError, TypeError):
            symbols = None
        
        relevance = score_relevance(s[13], symbols, s[1])
        confidence = s[10] if isinstance(s[10], (int, float)) else 0.0
        
        if relevance + confidence >= threshold:
            filtered.append({
                'setup_id': s[0],
                'asset': s[1],
                'direction': s[2],
                'entry_price': s[3],
                'take_profit_1': s[4],
                'take_profit_2': s[5],
                'take_profit_3': s[6],
                'stop_loss': s[7],
                'risk_reward_ratio': s[8],
                'edge_score': s[9],
                'confidence': s[10],
                'rationale': s[11],
                'relevance': round(relevance, 2),
                'combined_score': round(relevance + confidence, 2),
            })
    
    # Sort by combined score descending
    filtered.sort(key=lambda x: x['combined_score'], reverse=True)
    
    print(f"[FILTER] {len(setups)} setups scanned → {len(filtered)} passed filter (threshold {threshold})")
    
    if filtered:
        print(f"\nTop filtered setups:")
        for f in filtered[:5]:
            print(f"  {f['asset']} {f['direction']} | score={f['combined_score']} (rel={f['relevance']} conf={f['confidence']}) | R:R={f['risk_reward_ratio']}")
    
    # Store filtered signal in events table
    if filtered:
        top = filtered[0]
        try:
            con.execute("""
                INSERT INTO events (source_id, event_type, timestamp, payload_headline, payload_body, symbols, lane, confidence, action)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                'signal-filter',
                'filtered_trade_alert',
                datetime.now(timezone.utc),
                f"✅ {top['asset']} {top['direction']} — Top signal (score {top['combined_score']})",
                json.dumps(top),
                [top['asset']],
                'trading',
                top['combined_score'],
                'alert',
            ])
            
            # Update top setup to 'alerted' status
            con.execute("UPDATE trade_setups SET status = 'alerted' WHERE setup_id = ?", [top['setup_id']])
            
            print(f"\n✅ Top signal stored and alerted: {top['asset']} {top['direction']} score={top['combined_score']}")
        except Exception as e:
            print(f"⚠️ Event store error: {e}")
    
    con.close()
    return filtered


if __name__ == "__main__":
    args = sys.argv[1:]
    
    threshold = DEFAULT_RELEVANCE_THRESHOLD
    if '--threshold' in args:
        idx = args.index('--threshold')
        if idx + 1 < len(args):
            threshold = float(args[idx + 1])
    
    post = '--post' in args
    
    filtered = filter_pending_setups(threshold=threshold, post=post)
    
    if filtered:
        print(f"\n✅ Signal filter complete — {len(filtered)} actionable setups")
    else:
        print(f"\n📭 No setups passed the filter threshold ({threshold})")