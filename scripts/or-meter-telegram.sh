#!/usr/bin/env bash
# Runs or-meter.sh and posts result to Telegram AI Hangout
set -euo pipefail

# Use OpenClaw bot token from config (this group's bot)
CHAT_ID="-5087043705"
BOT_TOKEN="8692705040:AAHJGoU8NVi7InCV56jPEqtXXlQdFDTx_KQ"

# Generate the meter text
METER_TEXT=$(bash /home/synczus/kestrel/scripts/or-meter.sh 2>/dev/null) || {
    echo "Meter failed"
    exit 1
}

# Post to Telegram
curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -d "chat_id=${CHAT_ID}" \
    -d "text=${METER_TEXT}" \
    -d "parse_mode=Markdown" \
    -o /dev/null

echo "Posted at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
