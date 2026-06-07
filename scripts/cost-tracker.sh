#!/bin/bash
# Cost tracker — logs per-cron and total OpenRouter spend estimates
# Writes to event-bus.md and or-budget-state.json
set -euo pipefail

EVENT_BUS="/home/synczus/kestrel/event-bus.md"
OR_STATE="/home/synczus/kestrel/or-budget-state.json"
CRON_HEALTH="/home/synczus/kestrel/cron-health"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Count how many times each cron ran since last check
# by reading heartbeat epochs
if [ -d "$CRON_HEALTH" ]; then
    NOW=$(date +%s)
    TOTAL_RUNS=0
    TOTAL_COST=0
    
    for HB in "$CRON_HEALTH"/*.heartbeat; do
        [ -f "$HB" ] || continue
        NAME=$(basename "$HB" .heartbeat)
        LAST_EPOCH=$(python3 -c "import json; print(json.load(open('$HB'))['epoch'])" 2>/dev/null || echo "0")
        
        # If heartbeat is fresh (< 24h), count it
        if [ "$LAST_EPOCH" != "0" ]; then
            AGE=$(( NOW - LAST_EPOCH ))
            if [ "$AGE" -lt 86400 ]; then
                TOTAL_RUNS=$(( TOTAL_RUNS + 1 ))
            fi
        fi
    done
    
    # Estimate: ~$0.002 per agent turn
    ESTIMATED=$(echo "scale=4; $TOTAL_RUNS * 0.002" | bc)
    TOTAL_COST=$(echo "scale=2; $ESTIMATED" | bc)
    
    # Read OR state for actual spend
    ACTUAL_DAILY="unknown"
    if [ -f "$OR_STATE" ]; then
        ACTUAL_DAILY=$(python3 -c "import json; d=json.load(open('$OR_STATE')); print(d.get('daily','unknown'))" 2>/dev/null || echo "unknown")
    fi
    
    LOG_LINE="${TIMESTAMP} | cost-tracker | ~${TOTAL_RUNS} cron runs | est: \$${TOTAL_COST}/day | OR actual: \$${ACTUAL_DAILY}"
    echo "$LOG_LINE" >> "$EVENT_BUS"
    echo "$LOG_LINE"
fi