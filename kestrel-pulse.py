#!/usr/bin/env python3
"""Kestrel Market Pulse — Telegram-ready. Fetches from Coinbase public API + Striker disk signals."""
import json, urllib.request, time, subprocess
from pathlib import Path

COINBASE = "https://api.exchange.coinbase.com/products"
SYMBOLS = {"BTC":"BTC-USD","ETH":"ETH-USD","SOL":"SOL-USD","DOGE":"DOGE-USD","XRP":"XRP-USD"}
SIGNAL_FILE = Path.home() / "kestrel/signals/.last_alert.json"

def fetch_stats(sym):
    try:
        req = urllib.request.Request(f"{COINBASE}/{sym}/stats",
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as r:
            d = json.loads(r.read().decode())
            o, h, l, last = float(d["open"]), float(d["high"]), float(d["low"]), float(d["last"])
            v = float(d["volume"])
            chg = round((last - o) / o * 100, 2) if o else 0
            return {"symbol": sym.replace("-USD",""), "price": last, "high": h, "low": l, "open": o, "change_pct": chg, "volume": v}
    except: return None

def get_signals():
    try:
        return [{"symbol":k,"move_pct":round(v[0],2)} for k,v in json.loads(SIGNAL_FILE.read_text()).items()]
    except: return []

def fmt(n):
    return "--" if n is None else f"${n:,.2f}" if abs(n) >= 1 else f"${n:.4f}"

def fmt_pct(n):
    return "--" if n is None else f"+{n:.2f}%" if n > 0 else f"{n:.2f}%"

def build_pulse():
    # Fetch all tickers in parallel-ish
    results = {}
    for name, sym in SYMBOLS.items():
        r = fetch_stats(sym)
        if r: results[name] = r
        time.sleep(0.1)  # pace

    signals = get_signals()
    
    if not results:
        return "⚠️ **KESTREL PULSE** — All data sources unavailable"
    
    # Compute directional verdict
    bullish = sum(1 for r in results.values() if r["price"] > r["open"])
    total = len(results)
    v_label = "IN" if bullish >= total * 0.6 else "OUT" if bullish <= total * 0.3 else "HOLD"
    v_icon = {"IN":"🟢","OUT":"🔴","HOLD":"🟡"}[v_label]
    
    lines = [f"{v_icon} **KESTREL PULSE** — {v_label}", ""]
    
    # Key markets
    lines.append("📊 **Key Markets** (Coinbase)")
    for name in ["BTC","ETH","SOL","DOGE","XRP"]:
        r = results.get(name)
        if not r: continue
        arrow = "▲" if r["change_pct"] >= 0 else "▼"
        chg = fmt_pct(r["change_pct"])
        hi_lo = f"H {fmt(r['high'])}  L {fmt(r['low'])}"
        lines.append(f"`{name:6s}` {fmt(r['price']):>10s}  {chg:>8s} {arrow}  {hi_lo}")
    lines.append("")
    
    # Live signals from Striker
    if signals:
        lines.append("⚡ **Live Signals** (Striker)")
        for s in signals:
            lines.append(f"  {'🔴' if s['move_pct']<0 else '🟢'} `{s['symbol']:6s}` {s['move_pct']:.2f}%")
        lines.append("")
    
    # Striker health from journal
    try:
        hlth = subprocess.run(["journalctl","-u","kestrel-striker","--since","1 minute ago","--no-pager","-o","cat"],
                              capture_output=True,text=True,timeout=5)
        hl = [l for l in hlth.stdout.splitlines() if "Health" in l and "ticks_processed" in l]
        if hl:
            pts = hl[-1].split("|")
            ticks = pts[1].split("=")[1].strip()
            queue = pts[2].split("=")[1].strip()
            lines.append(f"🔭 **Striker**: {ticks} ticks  |  queue: {queue}")
    except: pass
    
    lines.append(f"\n🔄 Coinbase direct  |  `/pulse`")
    return "\n".join(lines)

if __name__ == "__main__":
    print(build_pulse())