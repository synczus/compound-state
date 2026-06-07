#!/bin/bash
# OpenRouter Budget Monitor — checks daily spend, alerts if over threshold
set -euo pipefail

ENV_FILE="/home/synczus/.hermes/.env"
THRESHOLD=10.00
STATE_FILE="/home/synczus/kestrel/or-budget-state.json"
FLAG_FILE="/tmp/or-exceeded-flag"

# Extract API key from env file
KEY=$(grep '^OPENROUTER_API_KEY=' "$ENV_FILE" | head -1 | cut -d= -f2-)
[ -z "$KEY" ] && { echo "ERROR: No OPENROUTER_API_KEY found"; exit 1; }

# Fetch usage from OpenRouter
DATA=$(curl -sf -H "Authorization: Bearer $KEY" https://openrouter.ai/api/v1/auth/key 2>/dev/null) || {
  echo "ERROR: OpenRouter API call failed"
  exit 2
}

# Parse values with python3
DAILY=$(echo "$DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['data'].get('usage_daily',0))" 2>/dev/null || echo "0")
WEEKLY=$(echo "$DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['data'].get('usage_weekly',0))" 2>/dev/null || echo "0")
MONTHLY=$(echo "$DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['data'].get('usage_monthly',0))" 2>/dev/null || echo "0")

# Determine if over threshold
EXCEEDED="false"
if python3 -c "exit(0 if $DAILY > $THRESHOLD else 1)" 2>/dev/null; then
  EXCEEDED="true"
fi

# Write state file
cat > "$STATE_FILE" << JSONEOF
{
  "daily": $DAILY,
  "weekly": $WEEKLY,
  "monthly": $MONTHLY,
  "threshold": $THRESHOLD,
  "exceeded": $EXCEEDED,
  "checked_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
JSONEOF

# Edge-triggered alert — only on first exceedance
if [ "$EXCEEDED" = "true" ]; then
  if [ ! -f "$FLAG_FILE" ]; then
    echo "WARN: OpenRouter daily spend \$$DAILY exceeds \$$THRESHOLD threshold — set dashboard cap at https://openrouter.ai/settings/billing"
    date -u +%s > "$FLAG_FILE"
  fi
else
  rm -f "$FLAG_FILE"
fi

echo "OK"