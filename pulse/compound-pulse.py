#!/usr/bin/env python3
"""Compound Pulse v0.1 — every 30 min, checks hop state, signal pipeline, health.
Produces: P0 (urgent), P1 (active), P2 (infra). Appends to master-todo.md."""

import json, os, sqlite3, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path("/home/synczus/kestrel")
TODO = BASE / "master-todo.md"
HOP = BASE / "cycle-state" / "hop-sequence.json"
STRIKER_DB = BASE / "kestrel_signals.db"
COORD = BASE / "manifests" / "coordination.yaml"
INBOUND = Path("/home/synczus/.openclaw/media/inbound")

def read_json(path):
    try: return json.loads(Path(path).read_text())
    except: return {}

def pulse():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    items = []

    # ── 1. Hop State ─────────────────────────────────────────────────
    hop = read_json(HOP)
    if hop.get("complete") and hop.get("auto"):
        ago = time.time()
        idle = hop.get("idle_since", now)
        try:
            idle_dt = datetime.strptime(idle, "%Y-%m-%dT%H:%M:%SZ")
            ago = (datetime.now(timezone.utc) - idle_dt).total_seconds() / 60
        except: pass
        if ago > 25:
            items.append({"P": 1, "tag": "hop", "text": f"Hop idle {ago:.0f} min — propose next cycle"})
        else:
            items.append({"P": 2, "tag": "hop", "text": f"Hop idle ({ago:.0f} min), waiting for auto threshold"})
    elif hop.get("active"):
        step = hop.get("current_step", 0)
        chain = hop.get("chain", [])
        turn = chain[step] if step < len(chain) else "unknown"
        items.append({"P": 0, "tag": "hop", "text": f"Active hop — {turn}'s turn: {hop.get('query', '')[:60]}"})

    # ── 2. Striker Signals ────────────────────────────────────────────
    if STRIKER_DB.exists():
        try:
            db = sqlite3.connect(str(STRIKER_DB))
            c = db.execute("SELECT COUNT(*) FROM signals")
            total = c.fetchone()[0]
            c = db.execute("SELECT COUNT(*) FROM signals WHERE move_pct >= 0.3")
            gt03 = c.fetchone()[0]
            c = db.execute("SELECT datetime(MAX(timestamp)/1000000000, 'unixepoch') FROM signals")
            last = c.fetchone()[0]
            db.close()
            items.append({"P": 2, "tag": "striker", "text": f"{total} signals ({gt03} >=0.3%), last {last}"})
        except Exception as e:
            items.append({"P": 2, "tag": "striker", "text": f"DB error: {e}"})

    # ── 3. Coordination Router ───────────────────────────────────────
    router = BASE / "scripts" / "ingestion" / "router.py"
    if not router.exists():
        items.append({"P": 1, "tag": "router", "text": "Router not built yet — needs ship"})

    coord = read_json(COORD) if COORD.exists() else {}
    if not coord.get("signal_ingestion"):
        items.append({"P": 1, "tag": "contract", "text": "coordination.yaml exists but may be misconfigured"})

    # ── 4. Pending Exports ───────────────────────────────────────────
    try:
        exports = [f for f in INBOUND.iterdir() if f.suffix in (".html", ".txt", ".jsonl")]
        if exports:
            names = [e.name[:30] for e in exports]
            items.append({"P": 2, "tag": "exports", "text": f"{len(exports)} unprocessed: {', '.join(names[:3])}" + ("..." if len(names)>3 else "")})
    except: pass

    # ── 5. Service Health ────────────────────────────────────────────
    services = {"kestrel-striker.service": "Striker"}
    for svc, label in services.items():
        r = subprocess.run(["systemctl", "is-active", svc], capture_output=True, text=True)
        if r.stdout.strip() != "active":
            items.append({"P": 0, "tag": "health", "text": f"{label} is {r.stdout.strip()} — needs attention"})

    # ── OR Meter ────────────────────────────────────────────────────
    meter = BASE / "meter" / "state.json"
    if meter.exists():
        try:
            m = json.loads(meter.read_text())
            pct = m.get("pct", 0)
            if pct > 80:
                items.append({"P": 1, "tag": "budget", "text": f"OR at {m.get('current',0):.1f}/{m.get('cap',50):.0f} ({pct:.0f}%)"})
        except: pass

    # ── Sort & Write ─────────────────────────────────────────────────
    items.sort(key=lambda x: (x["P"], x["tag"]))
    p0 = [i for i in items if i["P"] == 0]
    p1 = [i for i in items if i["P"] == 1]
    p2 = [i for i in items if i["P"] == 2]

    summary = f"""# Compound Pulse — {now}

## P0 — Urgent
""" + "\n".join(f"- [{x['tag']}] {x['text']}" for x in p0) + "\n\n## P1 — Active\n" + "\n".join(f"- [{x['tag']}] {x['text']}" for x in p1) + "\n\n## P2 — Infra\n" + "\n".join(f"- [{x['tag']}] {x['text']}" for x in p2) + "\n"

    # Append to master-todo.md
    entry = f"\n--- pulse {now} ---\n"
    for x in items:
        entry += f"- [ ] {'🔴' if x['P']==0 else '🟡' if x['P']==1 else '⚪'} {x['tag']}: {x['text']}\n"
    with open(TODO, "a") as f:
        f.write(entry)

    # Also write structured signal doc
    pulse_dir = BASE / "pulse"
    pulse_dir.mkdir(exist_ok=True)
    signal_doc = pulse_dir / f"signal-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}.json"
    with open(signal_doc, "w") as f:
        json.dump({"timestamp": now, "p0": p0, "p1": p1, "p2": p2}, f, indent=2)

    # Print summary for stdout / cron capture
    print(summary)
    return 0

if __name__ == "__main__":
    sys.exit(pulse())