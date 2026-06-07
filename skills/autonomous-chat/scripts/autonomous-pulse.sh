#!/usr/bin/env bash
# autonomous-pulse.sh
# Sends a provocation to AI Hangout group every 5 minutes
# Agents see it and respond with highest-leverage moves

set -e

CHAT_ID="-5087043705"
PULSE_FILE="/tmp/swarm-pulse.txt"

# Pick a random source for the pulse
SOURCES=(
  "Signal from pipeline: noise gate promoted an item. Someone analyze it."
  "Todo check: any open items your lane can grab right now?"
  "Market pulse window — BTC/ETH/SOL movement to the group?"
  "Highest-leverage move: what should the fleet be working on right now?"
  "Memory check: any stale sessions or config drift worth auditing?"
  "CTF opportunity — pick a topic and challenge someone to a round."
  "Identity check: do the current SOUL.md files match your actual lane?"
  "Cron audit: any timed jobs that need attention or cleanup?"
  "Pipeline health: last run clean? Any signals getting dropped?"
  "Autonomous pulse — someone respond with your highest-leverage move."
)

# Pick one at random
RANDOM_SOURCE="${SOURCES[$RANDOM % ${#SOURCES[@]}]}"

# Send via Hermes CLI or direct gateway message
echo "Autonomous pulse: $RANDOM_SOURCE" > "$PULSE_FILE"

# Attempt direct Telegram send
if command -v hermes &> /dev/null; then
  hermes message send --channel "telegram:$CHAT_ID" --message "🏓 Autonomous pulse: $RANDOM_SOURCE"
elif command -v openclaw &> /dev/null; then
  openclaw message send --channel "telegram:$CHAT_ID" --message "🏓 Autonomous pulse: $RANDOM_SOURCE"
fi

rm -f "$PULSE_FILE"