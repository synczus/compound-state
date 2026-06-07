#!/bin/bash
# OpenRouter credit meter — posts daily usage bar to chat
# Cap reads from kestrel/meter/config.json — edit that file to change

OR_KEY=$(grep -oP 'OPENROUTER_API_KEY=\K.*' /home/synczus/.hermes/.env 2>/dev/null | head -1)
if [ -z "$OR_KEY" ]; then
  echo '{"error":"no key"}'
  exit 1
fi

RESP=$(curl -s --max-time 10 "https://openrouter.ai/api/v1/auth/key" \
  -H "Authorization: Bearer $OR_KEY")

DAILY=$(echo "$RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"{d['data']['usage_daily']:.2f}\")" 2>/dev/null || echo "0")
MONTHLY=$(echo "$RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"{d['data']['usage_monthly']:.2f}\")" 2>/dev/null || echo "0")

# Read cap from config file, fall back to $30
CAP=$(python3 -c "
import json
try:
    with open('/home/synczus/kestrel/meter/config.json') as f:
        c = json.load(f)
    print(c.get('daily_cap', 30.00))
except:
    print('30.00')
" 2>/dev/null || echo "30.00")

python3 -c "
import json, math
daily = float('$DAILY')
monthly = float('$MONTHLY')
cap = float('$CAP')
remaining = round(cap - daily, 2)

filled = min(int(cap), max(0, int(daily)))
empty = int(cap) - filled
if empty < 0: empty = 0
bar = '\u2588' * filled + '\u2591' * empty

warn = ''
if remaining < 5:
    warn = '\u26a0\ufe0f Low!'
if remaining < 0:
    warn = '\ud83d\udd34 OVER CAP'

msg = '**OpenRouter Meter**\n'
msg += '\`\`\`\n'
msg += f'\${daily:.2f} / \${cap:.2f} today {warn}\n'
msg += f'{bar}\n'
msg += f'\${remaining:.2f} remaining\n'
msg += f'\${monthly:.2f} this cycle\n'
msg += '\`\`\`'
print(json.dumps({
    'daily': daily,
    'remaining': remaining,
    'monthly': monthly,
    'bar': msg
}))
"