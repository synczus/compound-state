#!/usr/bin/env bash
# Run compound pulse check and post P0/P1 items to Telegram
set -euo pipefail

# Use OpenClaw bot token from config (this group's bot)
CHAT_ID="-5087043705"
BOT_TOKEN="8692705040:AAHJGoU8NVi7InCV56jPEqtXXlQdFDTx_KQ"
LOG="/home/synczus/kestrel/logs/compound-pulse.log"

# Run the python pulse
PULSE_OUTPUT=$(python3 /home/synczus/kestrel/pulse/compound-pulse.py 2>/dev/null)

# Check if there are P0 or P1 items
HAS_P0=$(echo "$PULSE_OUTPUT" | grep -c "P0 — Urgent" || true)
HAS_P1=$(echo "$PULSE_OUTPUT" | grep -c "P1 — Active" || true)

# Extract the P0 and P1 items (lines starting with - [ or - for items)
P0_ITEMS=$(echo "$PULSE_OUTPUT" | sed -n '/## P0/,/## P1/p' | grep '^- \[' | grep -v '^$' || true)
P1_ITEMS=$(echo "$PULSE_OUTPUT" | sed -n '/## P1/,/## P2/p' | grep '^- \[' | grep -v '^$' || true)

# Build message
MSG=""
if [ -n "$P0_ITEMS" ]; then
    MSG="${MSG}🔴 *P0 Items:*\n$P0_ITEMS\n\n"
fi
if [ -n "$P1_ITEMS" ]; then
    MSG="${MSG}🟡 *P1 Items:*\n$P1_ITEMS\n\n"
fi

if [ -n "$MSG" ]; then
    # Post to Telegram
    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d "chat_id=${CHAT_ID}" \
        -d "text=${MSG}" \
        -d "parse_mode=Markdown" \
        -o /dev/null
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) Posted P0/P1 items" >> "$LOG"
else
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) All quiet — nothing urgent" >> "$LOG"
fi
