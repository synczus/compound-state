#!/bin/bash
# boot-improvement-context.sh
# Called by any agent at session start.
# Returns 2-3 sentences of improvement context from feedback.duckdb + AgentMemory.
# Usage: python3 /home/synczus/kestrel/scripts/auto-improve/cycle-improver.py --agent <agent_name>

set -euo pipefail

AGENT="${1:-}"
if [ -z "$AGENT" ]; then
    echo "Usage: boot-improvement-context.sh <agent_name>"
    echo "  agent_name: openclaw, nemoclaw, kairos, shannon, hermes"
    exit 1
fi

cd /home/synczus/kestrel/scripts/auto-improve
python3 cycle-improver.py --agent "$AGENT" 2>/dev/null || echo ""
echo ""
echo "--- Lessons from AgentMemory ---"
# Use agentmemory to recall relevant lessons
# (agents do this natively with agentmemory__memory_lesson_recall)
echo "Run: agentmemory__memory_lesson_recall(query=\"$AGENT context\")"