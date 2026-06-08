#!/usr/bin/env bash
# or-budget-monitor — checks OpenRouter daily/monthly spend, writes heartbeat + state
set -euo pipefail

KESTREL="/home/synczus/kestrel"
HEARTBEAT_DIR="$KESTREL/cron-health"
STATE_FILE="$KESTREL/or-budget-state.json"

mkdir -p "$HEARTBEAT_DIR"

# Run the OpenRouter budget check
python3 "$KESTREL/scripts/openrouter-budget.py" 2>&1 || true

# Then also update or-budget-state.json with daily/weekly/monthly aggregates
# Pull from the data file written by openrouter-budget.py
DATA_FILE="$KESTREL/data/openrouter-budget.json"
if [ -f "$DATA_FILE" ]; then
    python3 -c "
import json
from datetime import datetime, timezone

with open('$DATA_FILE') as f:
    d = json.load(f)

usage = d.get('usage', 0)
limit = d.get('limit', 30)
remaining = d.get('remaining', 0)

state = {
    'daily': round(usage, 6),
    'weekly': round(usage * 7, 6),
    'monthly': round(usage * 30, 6),
    'threshold': 30.00,
    'exceeded': usage > 30,
    'checked_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
}

with open('$STATE_FILE', 'w') as f:
    json.dump(state, f, indent=2)
print(f'or-budget-state: \${usage:.2f} used, \${remaining:.2f} remaining')
"
fi

# Write heartbeat
EPOCH=$(date -u +%s)
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat > "$HEARTBEAT_DIR/or-budget-monitor.heartbeat" <<EOF
{
  "name": "or-budget-monitor",
  "status": "ok",
  "last_run": "$TS",
  "epoch": $EPOCH
}
EOF