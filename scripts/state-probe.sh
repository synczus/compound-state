#!/bin/bash
# State Probe v1 — live verification of compound state
# Updates cycle-state/current.json with verified facts
set -euo pipefail

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EVENT_BUS="/home/synczus/kestrel/event-bus.md"
CURRENT="/home/synczus/kestrel/cycle-state/current.json"

# Check Striker
STRIKER_STATUS="offline"
STRIKER_PID=""
if systemctl --user is-active kestrel-striker.service &>/dev/null; then
    STRIKER_STATUS="online"
    STRIKER_PID=$(systemctl --user show kestrel-striker.service -p MainPID --value 2>/dev/null)
fi

# Check WolfWatch
WOLFWATCH_STATUS="offline"
if curl -sf http://127.0.0.1:18790/health >/dev/null 2>&1; then
    WOLFWATCH_STATUS="online"
fi

# Check meta-monitor heartbeat freshness
META_MONITOR_AGE="unknown"
if [ -f "/home/synczus/kestrel/cron-health/meta-monitor.heartbeat" ]; then
    LAST_EPOCH=$(python3 -c "import json; print(json.load(open('/home/synczus/kestrel/cron-health/meta-monitor.heartbeat'))['epoch'])" 2>/dev/null)
    if [ -n "$LAST_EPOCH" ]; then
        META_MONITOR_AGE=$(( $(date +%s) - LAST_EPOCH ))
    fi
fi

# Write verified state
cat > "$CURRENT" <<STATE
{
  "timestamp": "${TIMESTAMP}",
  "verified": true,
  "services": {
    "striker": {
      "status": "${STRIKER_STATUS}",
      "pid": "${STRIKER_PID}"
    },
    "wolfwatch": {
      "status": "${WOLFWATCH_STATUS}"
    }
  },
  "meta_monitor_age_seconds": ${META_MONITOR_AGE:-null},
  "agents": [
    "hermes", "openclaw", "nemoclaw", "kairos", "shannon"
  ],
  "corrections": []
}
STATE

# Log
echo "${TIMESTAMP} | state-probe | Striker=${STRIKER_STATUS} WolfWatch=${WOLFWATCH_STATUS} MetaAge=${META_MONITOR_AGE}s" >> "$EVENT_BUS"
echo "State probe complete: Striker=${STRIKER_STATUS} WolfWatch=${WOLFWATCH_STATUS}"