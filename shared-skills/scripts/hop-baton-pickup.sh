#!/bin/bash
# Hop Baton Pickup — claim the active baton and print context
# Usage: hop-baton-pickup.sh <agent_name>
set -euo pipefail

BATON="/home/synczus/kestrel/active-baton.json"
AGENT="${1:-}"

if [ -z "$AGENT" ]; then
    echo "Usage: hop-baton-pickup.sh <agent_name>"
    exit 1
fi

if [ ! -f "$BATON" ]; then
    echo "ERROR: No active baton found at $BATON"
    exit 2
fi

# Validate
python3 "/home/synczus/kestrel/shared-skills/scripts/hop-baton-validator.py" "$BATON"

# Read and update current_agent
BATON_JSON=$(python3 -c "
import json
b = json.load(open('$BATON'))
print(json.dumps(b, indent=2))
echo "$BATON_JSON" | python3 -c "
import json, sys
b = json.load(sys.stdin)
prev = b['current_agent']
b['previous_agent'] = prev if prev and prev != 'none' else b['previous_agent']
b['current_agent'] = '$AGENT'
if b['cycle_id'] == 'parked':
    print(f'⚠️  Baton is PARKED — no active cycle. Use hop-baton-init.py to start one.')
    print(f'   Last parked reason: {b[\"next_agent_routing\"].get(\"reason_for_next_hop\", \"N/A\")}')
else:
    print(f'✅ {AGENT} picked up baton for cycle: {b[\"cycle_id\"]}')
    print(f'   Stage: {b[\"stage\"]}')
    print(f'   Previous agent: {b[\"previous_agent\"]}')
    print(f'   Work: {b[\"mission\"][\"selected_work_item\"]}')
    print(f'   Type: {b[\"mission\"][\"mission_type\"]}')
    print(f'   Next: {b[\"next_agent_routing\"][\"next_agent_name\"]}')
json.dump(b, open('$BATON', 'w'), indent=2)
"