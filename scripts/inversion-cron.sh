#!/bin/bash
# Inversion cron — runs every 10 min, reads current hop state,
# calls Perplexity to stress-test the active work item.
# Run via crontab: */10 * * * * /home/synczus/kestrel/scripts/inversion-cron.sh

HOP_FILE="/home/synczus/kestrel/cycle-state/hop-sequence.json"
SCRIPT="/home/synczus/kestrel/scripts/perplexity_search.py"
PULSES="/home/synczus/kestrel/agent-pulses/$(date +%Y-%m-%d)"

mkdir -p "$PULSES"

# Read current hop query
QUERY=$(python3 -c "
import json
with open('$HOP_FILE') as f:
    h = json.load(f)
print(h.get('query', 'No active work item'))
" 2>/dev/null)

# Invert it — stress test the assumptions
INVERSION=$(python3 "$SCRIPT" "Inversion analysis: The compound is currently working on this: '$QUERY'. Attack every assumption. What's wrong with this plan? What's being overlooked? What should they be doing instead? Be blunt." 2>/dev/null)

# Write inversion pulse
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "$TIMESTAMP | inversion-cron | $INVERSION" >> "$PULSES/inversion-pulse.md"

echo "Inversion complete"