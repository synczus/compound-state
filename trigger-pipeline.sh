#!/bin/bash
# Kestrel Pipeline Trigger — fires on-demand, then goes silent
# Usage: ./trigger-pipeline.sh "Your signal text here"
#
# Creates an issue for CEO, enables heartbeat temporarily,
# waits for completion, then disables heartbeat.

set -e

PAPERCLIP="http://127.0.0.1:3100"
COMPANY_ID="31ecf64c-e653-4047-80de-c7d02bb4bd8c"
CEO_ID="9f83b2a6-26fa-4c9f-9908-e2ec42de0f54"
SCOUT_ID="15af0bb2-6538-492d-9094-7a8ff6bff3cd"
POLISH_ID="9146f395-220c-418d-918f-a15818aaa722"
CRITIC_ID="d2084bd9-a1dc-45f2-bd6d-63a1567120b1"
GATE_ID="0ceae185-e564-4d34-a71e-2e43df99b6ac"

SIGNAL="${1:-}"

if [ -z "$SIGNAL" ]; then
    echo "Usage: $0 \"Your signal text\""
    exit 1
fi

echo "🐺🔥 FIRING KESTREL PIPELINE"
echo "Signal: $SIGNAL"
echo ""

# 1. Enable heartbeat on all pipeline agents (wake them up)
echo "→ Waking pipeline agents..."
for id in "$CEO_ID" "$SCOUT_ID" "$POLISH_ID" "$CRITIC_ID" "$GATE_ID"; do
    name=$(curl -s "$PAPERCLIP/api/agents/$id" | python3 -c "import sys,json; print(json.load(sys.stdin).get('name','?'))" 2>/dev/null)
    curl -s -X PATCH "$PAPERCLIP/api/agents/$id" \
        -H "Content-Type: application/json" \
        -d '{"runtimeConfig":{"heartbeat":{"enabled":true,"cooldownSec":1,"intervalSec":30,"wakeOnDemand":true,"maxConcurrentRuns":1}}}' \
        -o /dev/null -w "  $name: heartbeat ON (30s cycle)\n"
done

# 2. Create the issue assigned to CEO
echo "→ Creating issue..."
ISSUE=$(curl -s "$PAPERCLIP/api/companies/${COMPANY_ID}/issues" -X POST \
    -H "Content-Type: application/json" \
    -d "$(cat <<EOJSON
{
    "title": "PIPELINE: ${SIGNAL:0:80}",
    "description": "KESTREL PIPELINE SIGNAL\n\nSignal: ${SIGNAL}\n\nRoute through: CEO (decompose) → Scout (research) → Polish (synthesize) → Critic (stress-test) → Gate (verdict)\n\nPipeline must complete all 5 hops and return SHIP/KILL/ARCHIVE.",
    "assigneeAgentId": "${CEO_ID}",
    "priority": "high"
}
EOJSON
)" 2>&1)

ISSUE_ID=$(echo "$ISSUE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id','FAILED'))" 2>/dev/null)
IDENTIFIER=$(echo "$ISSUE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('identifier','?'))" 2>/dev/null)
echo "  Created: $IDENTIFIER ($ISSUE_ID)"
echo ""

# 3. Wait and monitor
echo "→ Monitoring pipeline (checking every 5s, timeout 120s)..."
START=$(date +%s)
TIMEOUT=120

while true; do
    NOW=$(date +%s)
    ELAPSED=$((NOW - START))
    if [ $ELAPSED -gt $TIMEOUT ]; then
        echo "  ⏰ TIMEOUT — pipeline exceeded ${TIMEOUT}s"
        break
    fi

    STATUS=$(curl -s "$PAPERCLIP/api/companies/${COMPANY_ID}/issues/${ISSUE_ID}" \
        | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','unknown'))" 2>/dev/null)

    echo "  [${ELAPSED}s] status=${STATUS}"

    if [ "$STATUS" = "completed" ] || [ "$STATUS" = "done" ] || [ "$STATUS" = "resolved" ] || [ "$STATUS" = "cancelled" ]; then
        echo ""
        echo "✅ Pipeline complete!"
        break
    fi

    sleep 5
done

# 4. Disable heartbeats again (go silent)
echo ""
echo "→ Returning agents to silent mode..."
for id in "$CEO_ID" "$SCOUT_ID" "$POLISH_ID" "$CRITIC_ID" "$GATE_ID"; do
    name=$(curl -s "$PAPERCLIP/api/agents/$id" | python3 -c "import sys,json; print(json.load(sys.stdin).get('name','?'))" 2>/dev/null)
    curl -s -X PATCH "$PAPERCLIP/api/agents/$id" \
        -H "Content-Type: application/json" \
        -d '{"runtimeConfig":{"heartbeat":{"enabled":false,"cooldownSec":0,"intervalSec":0,"wakeOnDemand":true,"maxConcurrentRuns":1}}}' \
        -o /dev/null -w "  $name: heartbeat OFF\n"
done

echo ""
echo "🐺🔥 Pipeline finished. Agents silent. Budget preserved."