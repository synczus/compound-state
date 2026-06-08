#!/usr/bin/env python3
"""
multi-tf-analyzer.py — Multi-Timeframe Analysis Engine

For every trade setup in the pipeline, this fetches live market data 
across 1h / 4h / 1d / 1w timeframes and computes:
  - Trend direction (vs SMA20/50)
  - RSI (14-period)
  - EMA cross status (12/26)
  - Volume profile
  - Combined MTA verdict + trade rationale

Integrates with:
  - trade-extractor.py (scored signals → structured setups)
  - DuckDB trade_setups table (writes MTA verdict per setup)
  - Signal filter (only emit setups for Chase's active watchlist)

Usage:
  python3 multi-tf-analyzer.py                     # Analyze all pending setups
  python3 multi-tf-analyzer.py --watch BTC,ETH,SOL  # Specific watchlist
  python3 multi-tf-analyzer.py --live               # Fetch + analyze all watched pairs live
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone

DB_PATH = "/home/synczus/kestrel/signals.duckdb"

# Chase's current watchlist (from Freqtrade config)
DEFAULT_WATCHLIST = ['BTC', 'ETH', 'SOL', 'LINK', 'XRP', 'ADA']

# EUR pairs on Kraken (best public data)
PAIR_MAP = {
    'BTC': 'BTC/USD',
    'ETH': 'ETH/USD',
    'SOL': 'SOL/USD',
    'XRP': 'XRP/USD',
    'ADA': 'ADA/USD',
    'DOGE': 'DOGE/USD',
    'DOT': 'DOT/USD',
    'LINK': 'LINK/USD',
    'AVAX': 'AVAX/USD',
}

TIMEFRAMES = ['1h', '4h', '1d', '1w']


def fetch_mta(asset, exchange=None):
    """Fetch multi-timeframe data for an asset and return structured MTA."""
    import ccxt
    
    if exchange is None:
        exchange = ccxt.kraken({'rateLimit': 1200})
    
    pair = PAIR_MAP.get(asset)
    if not pair:
        return None
    
    results = {}
    
    try:
        for tf in TIMEFRAMES:
            ohlcv = exchange.fetch_ohlcv(pair, timeframe=tf, limit=150)
            if not ohlcv:
                continue
            
            closes = [c[4] for c in ohlcv]
            current = closes[-1]
            prev = closes[-2] if len(closes) > 1 else current
            
            # SMA calculations
            sma20 = sum(closes[-20:]) / min(20, len(closes))
            sma50 = sum(closes[-50:]) / min(50, len(closes)) if len(closes) >= 50 else sma20
            
            # RSI 14
            gains, losses = [], []
            lookback = min(15, len(closes))
            for i in range(1, lookback):
                diff = closes[-i] - closes[-i-1]
                if diff > 0:
                    gains.append(diff)
                else:
                    losses.append(abs(diff))
            avg_g = sum(gains) / lookback if gains else 0
            avg_l = sum(losses) / lookback if losses else 0.001
            rsi = round(100 - (100 / (1 + avg_g / avg_l)), 1)
            
            # EMAs
            ema12 = sum(closes[-12:]) / 12
            ema26 = sum(closes[-26:]) / 26
            
            # Volume
            vols = [c[5] for c in ohlcv[-10:]]
            avg_vol = sum(vols) / len(vols) if vols else 1
            vol_ratio = round(vols[-1] / avg_vol, 2) if avg_vol > 0 else 1.0
            
            # Direction
            candle_change = round((current - prev) / prev * 100, 2)
            
            # Combined signal
            signal = 'NEUTRAL'
            if rsi > 70 and current > sma20:
                signal = 'OVERBOUGHT'
            elif rsi < 30 and current < sma20:
                signal = 'OVERSOLD'
            elif current > ema12 and ema12 > ema26:
                signal = 'BULLISH'
            elif current < ema12 and ema12 < ema26:
                signal = 'BEARISH'
            
            results[tf] = {
                'price': round(current, 2),
                'change_pct': candle_change,
                'rsi': rsi,
                'signal': signal,
                'sma20': round(sma20, 2),
                'sma50': round(sma50, 2),
                'volume_ratio': vol_ratio,
                'trend': 'BULLISH' if current > sma20 and sma20 > sma50 else 'BEARISH' if current < sma20 and sma20 < sma50 else 'NEUTRAL',
            }
    
    except Exception as e:
        print(f"[MTA] Error fetching {asset}: {e}", file=sys.stderr)
        return None
    
    return results


def generate_verdict(mta_data, setup_direction=None):
    """Generate a combined MTA verdict from all timeframe results."""
    if not mta_data:
        return 'NO DATA', 'Unable to fetch market data for analysis'
    
    signals = []
    for tf in TIMEFRAMES:
        if tf in mta_data:
            signals.append(mta_data[tf]['signal'])
    
    if not signals:
        return 'NO DATA', 'No timeframe data available'
    
    # Count bullish vs bearish
    bullish = sum(1 for s in signals if s == 'BULLISH')
    bearish = sum(1 for s in signals if s == 'BEARISH')
    oversold = 'OVERSOLD' in signals
    overbought = 'OVERBOUGHT' in signals
    
    # Detect bounce setup (oversold daily + bullish hourly)
    daily_signal = mta_data.get('1d', {}).get('signal', '')
    hourly_signal = mta_data.get('1h', {}).get('signal', '')
    weekly_signal = mta_data.get('1w', {}).get('signal', '')
    
    reasons = []
    
    if oversold and hourly_signal == 'BULLISH':
        verdict = 'BOUNCE SETUP'
        reasons.append('Daily oversold with hourly bullish reversal — classic bounce entry')
        if setup_direction == 'LONG':
            reasons.append(f'Direction matches: LONG confirmed by MTA')
        elif setup_direction == 'SHORT':
            reasons.append(f'⚠️ MTA shows oversold bounce — SHORT is counter-trend')
    elif overbought and hourly_signal == 'BEARISH':
        verdict = 'REJECTION SETUP'
        reasons.append('Daily overbought with hourly bearish — rejection forming')
    elif bullish >= 2 and bearish == 0:
        verdict = 'STRONG BULLISH'
        reasons.append(f'{bullish}/{len(signals)} timeframes bullish — clear uptrend momentum')
    elif bearish >= 2 and bullish == 0:
        verdict = 'STRONG BEARISH'
        reasons.append(f'{bearish}/{len(signals)} timeframes bearish — clear downtrend momentum')
    elif bullish > bearish:
        verdict = 'CAUTIOUS BULLISH'
        reasons.append(f'Mixed but tilt bullish ({bullish}-{bearish}) — trend favors longs')
    elif bearish > bullish:
        verdict = 'CAUTIOUS BEARISH'
        reasons.append(f'Mixed but tilt bearish ({bearish}-{bullish}) — trend favors shorts')
    else:
        verdict = 'MIXED'
        reasons.append(f'No clear edge ({bullish} bullish / {bearish} bearish) — range or chop')
    
    if weekly_signal == 'BEARISH' and verdict in ['STRONG BULLISH', 'CAUTIOUS BULLISH']:
        reasons.append(f'Warning: weekly is BEARISH — this is correction bounce, not trend reversal')
    
    return verdict, ' | '.join(reasons)


def format_mta_report(asset, mta_data, verdict, rationale):
    """Format MTA as a readable report card."""
    if not mta_data:
        return f"❌ {asset} — No market data available"
    
    lines = [f"📊 {asset} — MTA Report", "=" * 40]
    
    for tf in TIMEFRAMES:
        d = mta_data.get(tf)
        if not d:
            continue
        
        sig = d['signal']
        emoji = {'BULLISH': '🟢', 'BEARISH': '🔴', 'OVERSOLD': '🟢', 'OVERBOUGHT': '🟡', 'NEUTRAL': '⬜'}.get(sig, '⬜')
        rsi_str = f"RSI {d['rsi']}"
        if d['rsi'] > 70:
            rsi_str += ' 🔥'
        elif d['rsi'] < 30:
            rsi_str += ' ❄️'
        
        dir_emoji = '↗️' if d['change_pct'] > 0 else '↘️'
        lines.append(f"  {tf:4s} {emoji} ${d['price']:<9} {dir_emoji} {d['change_pct']:+.2f}% | {rsi_str:>12} | {sig}")
    
    lines.append("")
    verdict_emoji = {
        'BOUNCE SETUP': '🔄',
        'REJECTION SETUP': '⛔',
        'STRONG BULLISH': '🟢',
        'STRONG BEARISH': '🔴',
        'CAUTIOUS BULLISH': '🟡',
        'CAUTIOUS BEARISH': '🟠',
        'MIXED': '⬜',
    }.get(verdict, '❓')
    
    lines.append(f"  {verdict_emoji} VERDICT: {verdict}")
    lines.append(f"  {rationale}")
    
    return '\n'.join(lines)


def analyze_watchlist(watchlist=None):
    """Run full MTA on a watchlist and store results in DuckDB."""
    if watchlist is None:
        watchlist = DEFAULT_WATCHLIST
    
    import ccxt
    exchange = ccxt.kraken({'rateLimit': 1200})
    
    try:
        import duckdb
        con = duckdb.connect(DB_PATH)
    except Exception:
        con = None
    
    results = []
    
    for asset in watchlist:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Analyzing {asset}...")
        
        mta = fetch_mta(asset, exchange)
        if not mta:
            print(f"  ❌ Failed to fetch {asset}")
            continue
        
        verdict, rationale = generate_verdict(mta)
        report = format_mta_report(asset, mta, verdict, rationale)
        
        print(report)
        
        # Store in DuckDB
        if con:
            try:
                mta_id = f"mta_{uuid.uuid4().hex[:12]}"
                mta_json = json.dumps(mta)
                con.execute("""
                    INSERT INTO events (source_id, event_type, timestamp, payload_headline, payload_body, symbols, lane, confidence, action)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    'multi-tf-analyzer',
                    'mta_report',
                    datetime.now(timezone.utc),
                    f"{asset} MTA: {verdict}",
                    report,
                    [asset],
                    'analysis',
                    round(0.5 + 0.5 * (1 - abs(bearish_count(mta)) / 5), 2) if (bc := bearish_count(mta)) else 0.5,
                    verdict,
                ])
                print(f"  ✅ Stored to DuckDB")
            except Exception as e:
                print(f"  ⚠️ DuckDB write error: {e}")
        
        results.append({'asset': asset, 'mta': mta, 'verdict': verdict, 'rationale': rationale})
    
    if con:
        con.close()
    
    return results


def bearish_count(mta):
    """Count bearish signals across timeframes (negative = bearish tilt)."""
    bullish = sum(1 for tf in TIMEFRAMES if tf in mta and mta[tf]['signal'] == 'BULLISH')
    bearish = sum(1 for tf in TIMEFRAMES if tf in mta and mta[tf]['signal'] == 'BEARISH')
    return bearish - bullish


def analyze_pending_setups():
    """For each pending trade setup, add MTA context and update status."""
    try:
        import duckdb
        con = duckdb.connect(DB_PATH, read_only=True)
    except Exception as e:
        print(f"❌ Cannot connect to DuckDB: {e}")
        return
    
    # Get unique assets from pending trade setups
    assets = con.execute("""
        SELECT DISTINCT asset FROM trade_setups 
        WHERE status = 'pending'
        AND asset IS NOT NULL
        AND asset != 'UNKNOWN'
        ORDER BY asset
    """).fetchall()
    con.close()
    
    # Limit to known pairs + watchlist-aligned
    known_pairs = set(PAIR_MAP.keys())
    assets = [a[0] for a in assets if a[0] in known_pairs or a[0] in DEFAULT_WATCHLIST]
    assets = assets[:6]  # Cap API calls
    if not assets:
        print("[MTA] No pending setups to analyze")
        return
    
    print(f"[MTA] Analyzing {len(assets)} assets from pending setups: {', '.join(assets)}")
    
    import ccxt
    exchange = ccxt.kraken({'rateLimit': 1200})
    
    con = duckdb.connect(DB_PATH)
    
    for asset in assets:
        mta = fetch_mta(asset, exchange)
        if not mta:
            continue
        
        verdict, rationale = generate_verdict(mta)
        
        # Update all pending setups for this asset with MTA verdict
        con.execute("""
            UPDATE trade_setups 
            SET rationale = rationale || ' | MTA: ' || ? || ' — ' || ?,
                status = CASE 
                    WHEN ? IN ('STRONG_BULLISH', 'BOUNCE SETUP', 'CAUTIOUS BULLISH') AND direction = 'LONG' THEN 'confirmed'
                    WHEN ? IN ('STRONG_BEARISH', 'CAUTIOUS_BEARISH') AND direction = 'SHORT' THEN 'confirmed'
                    ELSE 'pending'
                END
            WHERE asset = ? AND status = 'pending'
        """, [verdict, rationale, verdict, verdict, asset])
        
        count = con.execute("SELECT COUNT(*) FROM trade_setups WHERE asset = ? AND status = 'confirmed'", [asset]).fetchone()[0]
        print(f"  {asset}: {verdict} — confirmed {count} setups")
    
    con.close()
    print(f"[MTA] Analysis complete")


if __name__ == "__main__":
    args = sys.argv[1:]
    
    if '--watch' in args:
        idx = args.index('--watch')
        watch = args[idx + 1].split(',') if idx + 1 < len(args) else DEFAULT_WATCHLIST
        analyze_watchlist(watch)
    elif '--pending' in args:
        analyze_pending_setups()
    elif '--live' in args:
        analyze_watchlist(DEFAULT_WATCHLIST)
    else:
        # Default: analyze pending setups + live watchlist
        analyze_pending_setups()
        analyze_watchlist(DEFAULT_WATCHLIST)