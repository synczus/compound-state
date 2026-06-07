#!/usr/bin/env bash
# Self-Healing Compound State Generator v0.1
# Reads: DuckDB signals table, Striker health file, systemd service states, OR budget
# Writes: /home/synczus/kestrel/cycle-state/current.json (single-file source of truth)
# Cron: */5 * * * * (or triggered by heartbeat)
# Dependency: pip3 install duckdb-cli or python3-duckdb

set -euo pipefail

KESTREL_DIR="/home/synczus/kestrel"
DB_PATH="${KESTREL_DIR}/signals.duckdb"
STATE_FILE="${KESTREL_DIR}/cycle-state/current.json"
HEALTH_DIR="${KESTREL_DIR}"

# ── Helper: fetch DuckDB row count per source_id ─────────────────
source_counts() {
    if [ -f "$DB_PATH" ]; then
        python3 -c "
import json, duckdb
try:
    con = duckdb.connect('$DB_PATH')
    rows = con.execute(\"\"\"SELECT source_id, lane, COUNT(*) as cnt
        FROM events GROUP BY source_id, LANE ORDER BY source_id\"\"\").fetchall()
    sources = {}
    for sid, lane, cnt in rows:
        if sid not in sources:
            sources[sid] = {}
        sources[sid][lane] = cnt
    print(json.dumps(sources))
except Exception as e:
    print(json.dumps({'error': str(e)}))
" 2>/dev/null || echo '{"error":"db_offline"}'
    else
        echo '{"error":"no_db"}'
    fi
}

# ── Helper: check systemd service ────────────────────────────────────
service_status() {
    local name="$1"
    if systemctl is-active --quiet "$name" 2>/dev/null; then
        echo "active"
    else
        echo "inactive"
    fi
}

# ── Helper: read Striker health file ──────────────────────────────────
striker_health() {
    local hf="${KESTREL_DIR}/striker_health.json"
    if [ -f "$hf" ]; then
        cat "$hf"
    else
        echo '{"error":"no_health_file"}'
    fi
}

# ── Helper: get OR budget remaining ────────────────────────────────────
or_budget() {
    local bf="${KESTREL_DIR}/../.hermes/budget-guard-state.json"
    if [ -f "$bf" ]; then
        python3 -c "
import json
d = json.load(open('$bf'))
print(json.dumps(d))
" 2>/dev/null || echo '{"error":"budget_parse"}'
    else
        echo '{"error":"no_budget_file"}'
    fi
}

# ── Build state JSON ──────────────────────────────────────────────────
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

STRIKER=$(striker_health)
BUDGET=$(or_budget)
SERVICES=$(systemctl list-units --type=service --state=running --no-legend 2>/dev/null | awk '{print $1}')
STRIKER_SVC=$(service_status "kestrel-striker")
WOLFWATCH_SVC=$(service_status "wolfwatch")

python3 <<PYEOF
import json, os

state = {
    "timestamp": "$NOW",
    "version": "0.1.0",
    "budget": json.loads('''$BUDGET'''),
    "services": {
        "striker": {"status": "$STRIKER_SVC", "health": json.loads('''$STRIKER''')},
        "wolfwatch": {"status": "$WOLFWATCH_SVC"}
    },
    "sources": json.loads('''$(source_counts)'''),
    "alerts": [],
    "agents": {
        "nemoclaw": {"status": "unknown", "last_heartbeat": ""},
        "kairos": {"status": "unknown", "last_heartbeat": ""},
        "kestrelmarkets": {"status": "unknown", "last_heartbeat": ""},
        "shannon": {"status": "disabled", "last_heartbeat": ""}
    }
}

# Budget alert
budget_remaining = state["budget"].get("usd_remaining", 999)
if isinstance(budget_remaining, (int, float)):
    if budget_remaining < 5:
        state["alerts"].append({"source": "budget", "severity": "warning", "reason": f"OR balance \${budget_remaining:.2f} — below \$5 threshold", "created_at": "$NOW"})
    if budget_remaining < 2:
        state["alerts"].append({"source": "budget", "severity": "critical", "reason": "OR balance below \$2 — guard will pause", "created_at": "$NOW"})

# Service alerts
if state["services"]["striker"]["status"] == "inactive":
    state["alerts"].append({"source": "striker", "severity": "error", "reason": "Striker service inactive", "created_at": "$NOW"})
if state["services"]["wolfwatch"]["status"] == "inactive":
    state["alerts"].append({"source": "wolfwatch", "severity": "warning", "reason": "WolfWatch service inactive", "created_at": "$NOW"})

os.makedirs(os.path.dirname("$STATE_FILE"), exist_ok=True)
with open("$STATE_FILE", "w") as f:
    json.dump(state, f, indent=2)

print(f"State written to {os.path.relpath('$STATE_FILE')}")
print(f"  Budget: \${budget_remaining if isinstance(budget_remaining, (int, float)) else '?'}")
print(f"  Striker: {state['services']['striker']['status']}")
print(f"  WolfWatch: {state['services']['wolfwatch']['status']}")
print(f"  Alerts: {len(state['alerts'])}")
PYEOF