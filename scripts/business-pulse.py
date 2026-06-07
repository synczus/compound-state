#!/usr/bin/env python3
"""
Business Pulse — every 6 hours, scans market data + boards + Striker signals
and posts ONE actionable item to the group. No noise, just the highest-leverage move.
"""
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

TODO = Path("/home/synczus/kestrel/master-todo.md")
STRIKER = Path("/home/synczus/kestrel/striker_health.json")
CYCLE = Path("/home/synczus/kestrel/cycle-state/current.json")
EVENT_BUS = Path("/home/synczus/kestrel/event-bus.md")

def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(EVENT_BUS, "a") as f:
        f.write(f"\n{ts} | business-pulse | {msg}")
    print(msg)

def get_market_pulse():
    try:
        result = subprocess.run(
            ["curl", "-s", "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd"],
            capture_output=True, text=True, timeout=10
        )
        prices = json.loads(result.stdout)
        btc = prices.get("bitcoin", {}).get("usd", "?")
        eth = prices.get("ethereum", {}).get("usd", "?")
        sol = prices.get("solana", {}).get("usd", "?")
        return f"BTC ${btc} | ETH ${eth} | SOL ${sol}"
    except Exception as e:
        return f"Market fetch failed: {e}"

def get_striker_status():
    if STRIKER.exists():
        try:
            data = json.loads(STRIKER.read_text())
            return f"Striker: {data.get('status','?')} | Signals: {data.get('total_signals',0)}"
        except:
            return "Striker: unknown"
    return "Striker: no data"

def get_board_summary():
    if not TODO.exists():
        return "Board: no master-todo.md"
    
    text = TODO.read_text()
    p0_pending = text.count("🔴") + text.count("🟡") * 0.5
    done = text.count("✅")
    
    items_p0 = []
    in_sprint3 = False
    for line in text.split("\n"):
        if "SPRINT 3" in line:
            in_sprint3 = True
        if in_sprint3 and line.startswith("|") and ("🔴" in line or "🟡" in line):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                items_p0.append(parts[2])
    
    top_item = items_p0[0] if items_p0 else "none"
    return f"Board: {done} done, {int(p0_pending)} pending. Top: {top_item}"

def main():
    market = get_market_pulse()
    striker = get_striker_status()
    board = get_board_summary()

    summary = f"📊 {market} | {striker} | {board}"
    log(summary)

    # Write to a file that can be consumed
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "market": market,
        "striker": striker,
        "board": board,
        "summary": summary
    }
    Path("/home/synczus/kestrel/dashboard/business-pulse.json").write_text(json.dumps(output, indent=2))

    # Write heartbeat
    hb_dir = Path("/home/synczus/kestrel/cron-health")
    hb_dir.mkdir(exist_ok=True)
    hb = {
        "name": "business-pulse",
        "status": "ok",
        "last_run": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "epoch": int(datetime.now(timezone.utc).timestamp())
    }
    (hb_dir / "business-pulse.heartbeat").write_text(json.dumps(hb, indent=2))

if __name__ == "__main__":
    main()