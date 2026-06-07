#!/usr/bin/env bash
# Kestrel Daily Digest — consolidated morning brief
# Run: bash /home/synczus/kestrel/daily-digest.sh
# Scheduled: 8am via daily-briefing cron
# On-demand: "run daily digest"

set -euo pipefail

DATE=$(date "+%Y-%m-%d")
COMPANY_ID="31ecf64c-e653-4047-80de-c7d02bb4bd8c"
PAPERCLIP="http://127.0.0.1:3100"

echo "🦅 KESTREL DAILY DIGEST — ${DATE}"
echo ""

# ── Market ──
echo "📈 Market"
STRIKER_LINES=$(journalctl -u kestrel-striker --since "24h ago" --no-pager -n 10 2>/dev/null | grep -E "HTTP Request|ticks|price" | tail -3 || true)
if [ -n "$STRIKER_LINES" ]; then
  echo "  Striker: $(journalctl -u kestrel-striker --since "24h ago" --no-pager 2>/dev/null | grep -cE 'HTTP Request|ticks' || echo 0) requests in 24h"
  echo "  Last: $(echo "$STRIKER_LINES" | tail -1 | sed 's/.*Request: //;s/\"HTTP.*//' | head -c 60)"
else
  echo "  Striker: no recent data"
fi

# ── Thought Inbox ──
echo ""
echo "🧠 Thought Inbox"
INBOX="/home/synczus/inbox.md"
if [ -f "$INBOX" ]; then
  TOTAL=$(grep -c "^2026" "$INBOX" 2>/dev/null || echo 0)
  echo "  ${TOTAL} thoughts captured"
  if [ "$TOTAL" -gt 0 ]; then
    grep "^2026" "$INBOX" | while IFS=' |' read -r ts time rest; do
      echo "  • ${rest:0:80}"
    done
  fi
else
  echo "  (no inbox file)"
fi

# ── Failures & Alerts (last 24h) ──
echo ""
echo "⚠️  Failures & Alerts"
SW_ALERTS=$(journalctl --user -u hermes-cron-service-watchdog.service --since "24h ago" --no-pager -o cat 2>/dev/null | grep -c "ALERT" || true)
PW_ALERTS=$(journalctl --user -u hermes-cron-pipeline-watchdog.service --since "24h ago" --no-pager -o cat 2>/dev/null | grep -c "ALERT" || true)
echo "  service-watchdog: ${SW_ALERTS} alerts"
echo "  pipeline-watchdog: ${PW_ALERTS} alerts"

# ── Budget ──
echo ""
echo "💰 Budget"
COST_DATA=$(curl -sf "http://127.0.0.1:3100/api/companies/${COMPANY_ID}" 2>/dev/null || echo "{}")
SPENT=$(echo "$COST_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin).get('spentMonthlyCents',0)/100)" 2>/dev/null || echo "0")
echo "  Spent: \$${SPENT}"
echo "  Budget: \$6.25"
REMAINING=$(python3 -c "print(round(6.25 - ${SPENT}, 4))" 2>/dev/null || echo "?")
echo "  Remaining: \$${REMAINING}"

# ── Pipeline Output ──
echo ""
echo "🔧 Pipeline Output (last 24h)"
curl -sf "${PAPERCLIP}/api/companies/${COMPANY_ID}/issues" 2>/dev/null | python3 -c "
import sys, json, os
issues = json.load(sys.stdin)
yesterday = '$DATE'
count = 0
for i in issues:
    updated = i.get('updatedAt', '')
    if yesterday in updated and i.get('status') == 'done':
        count += 1
        print(f\"  ✅ {i['identifier']} — {i['title'][:60]}\")
if count == 0:
    print('  No completions in last 24h')
" 2>/dev/null

# ── Agent Health ──
echo ""
echo "🤖 Agent Health"
curl -sf "${PAPERCLIP}/api/companies/${COMPANY_ID}/agents" 2>/dev/null | python3 -c "
import sys, json
agents = json.load(sys.stdin)
pipeline = {'Gemini-CEO','Perplexity-Scout','DeepSeek-Polish','DeepSeek-Critic','Claude-Gate'}
for a in agents:
    if a['name'] in pipeline:
        s = a.get('status','?')
        hb = a.get('lastHeartbeatAt','never')[:19] if a.get('lastHeartbeatAt') else 'never'
        icon = '🟢' if s == 'running' else '🔴'
        print(f\"  {icon} {a['name']:20s} status={s:10s} last_hb={hb}\")
" 2>/dev/null

# ── Services ──
echo ""
echo "🔌 Services"
for svc_spec in "Kestrel-API:8000" "Paperclip:3100"; do
  name="${svc_spec%%:*}"
  port="${svc_spec##*:}"
  http_code=$(curl -sf -o /dev/null -w "%{http_code}" --max-time 3 "http://127.0.0.1:${port}/" 2>/dev/null || echo "000")
  if [ "$http_code" = "200" ]; then
    echo "  🟢 $name (port ${port})"
  else
    echo "  🔴 $name (port ${port}) — HTTP ${http_code}"
  fi
done
if systemctl is-active --quiet kestrel-striker 2>/dev/null; then
  echo "  🟢 Striker"
else
  echo "  🔴 Striker — DOWN"
fi

echo ""
echo "═══════════════════════════════════════════"