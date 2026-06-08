#!/usr/bin/env bash
# OpenRouter Meter — generates bar chart of daily budget usage
set -euo pipefail

ENV_FILE="/home/synczus/.hermes/.env"
CAP=50.00

KEY=$(grep '^OPENROUTER_API_KEY=' "$ENV_FILE" | head -1 | cut -d= -f2-)
[ -z "$KEY" ] && { echo "NO_KEY"; exit 1; }

DATA=$(curl -sf -H "Authorization: Bearer $KEY" https://openrouter.ai/api/v1/auth/key 2>/dev/null) || { echo "API_ERROR"; exit 2; }

DAILY=$(echo "$DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['data'].get('usage_daily',0))" 2>/dev/null || echo "0")
MONTHLY=$(echo "$DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['data'].get('usage_monthly',0))" 2>/dev/null || echo "0")

python3 -c "
daily = float('$DAILY')
cap = float('$CAP')
monthly = float('$MONTHLY')
remaining = max(0, cap - daily)
pct = min(daily / cap * 100, 100)
full = int(pct / 5)
empty = 20 - full
bar = chr(9608) * full + chr(9617) * empty
print(f'OpenRouter Meter')
print(f'\${daily:.2f} / \${cap:.2f} today')
print(bar)
print(f'\${remaining:.2f} remaining')
print(f'\${monthly:.2f} this cycle')
"