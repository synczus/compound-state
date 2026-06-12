#!/bin/bash
# auto-git.sh — Auto-commit and push compound state changes
# v2 — with log rotation + push failure handling
# Runs via cron every 4 hours

REPO_DIR="/home/synczus/kestrel"
LOG_FILE="/home/synczus/kestrel/auto-git.log"
MAX_LOG_AGE_DAYS=7

# ── Maintenance ──
# Rotate logs older than 7 days in key log dirs
find /home/synczus/huntsystems/logs/cron/ -name "*.log" -mtime +$MAX_LOG_AGE_DAYS -delete 2>/dev/null
find /home/synczus/.hermes/logs/ -name "*.log" -mtime +$MAX_LOG_AGE_DAYS -delete 2>/dev/null
find /home/synczus/kestrel/ -name "auto-git.log*" -mtime +$MAX_LOG_AGE_DAYS -delete 2>/dev/null

# Clean up stale temp files
# Repo maintenance — auto gc if .git grows >50MB
cd "$REPO_DIR"
REPO_SIZE=$(du -s .git 2>/dev/null | cut -f1)
[ "$REPO_SIZE" -gt 50000 ] && git gc --auto 2>> "$LOG_FILE" && echo "$(date) — git gc (${REPO_SIZE}K)" >> "$LOG_FILE"
find /home/synczus/kestrel/ -name "*.tmp" -mtime +1 -delete 2>/dev/null
find /home/synczus/kestrel/ -name "*.bak" -mtime +1 -delete 2>/dev/null

# ── Git ──
cd "$REPO_DIR" || exit 1

if git status --short | grep -q .; then
    SUMMARY=$(git status --short | awk '{print $NF}' | tr '\n' ' ' | head -c 200)
    
    git add -A
    git commit -m "auto: compound state — $(date '+%Y-%m-%d %H:%M') — ${SUMMARY}"
    
    if git push origin main 2>> "$LOG_FILE"; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') — committed and pushed: ${SUMMARY}" >> "$LOG_FILE"
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') — PUSH FAILED: ${SUMMARY}" >> "$LOG_FILE"
        # Retry once after a brief wait
        sleep 5
        if git push origin main 2>> "$LOG_FILE"; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') — retry succeeded: ${SUMMARY}" >> "$LOG_FILE"
        else
            echo "$(date '+%Y-%m-%d %H:%M:%S') — PUSH FAILED after retry" >> "$LOG_FILE"
        fi
    fi
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') — no changes" >> "$LOG_FILE"
fi

# ── Heartbeat (for meta-monitor) ──
HEARTBEAT_DIR="/home/synczus/kestrel/cron-health"
mkdir -p "$HEARTBEAT_DIR"
cat > "$HEARTBEAT_DIR/auto-git-sync.heartbeat" <<EOF
{
  "name": "auto-git-sync",
  "status": "ok",
  "last_run": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "epoch": $(date +%s)
}
EOF