#!/bin/bash
# Hunter Poller — starts the GitHub commit hunter background poller if not already running.
# Modeled after inversion-cron.sh pattern.
# Run via crontab: @reboot /home/synczus/kestrel/scripts/hunter-poller.sh
# And periodic watchdog: */30 * * * * /home/synczus/kestrel/scripts/hunter-poller.sh

set -euo pipefail

KESTREL="/home/synczus/kestrel"
LOCK="/tmp/kestrel-hunter-poll.lock"
LOG="$KESTREL/logs/hunter-poller.log"
POLL_CMD="python3 main.py poll"

mkdir -p "$(dirname "$LOG")"

cd "$KESTREL"

if ! flock -n "$LOCK" -c "pgrep -f 'main.py poll' > /dev/null"; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) | Starting hunter poller (was not running)" >> "$LOG"
    # Use the project .venv if present, else system python (with deps)
    if [ -x "$KESTREL/.venv/bin/python3" ]; then
        PY="$KESTREL/.venv/bin/python3"
    else
        PY="python3"
    fi
    nohup $PY $POLL_CMD >> "$LOG" 2>&1 &
    disown || true
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) | Hunter poller started (pid $!)" >> "$LOG"
else
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) | Hunter poller already running" >> "$LOG"
fi
