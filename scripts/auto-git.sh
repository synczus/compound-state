#!/bin/bash
# auto-git.sh — Auto-commit and push compound state changes
# Runs via cron every 4 hours

REPO_DIR="/home/synczus/kestrel"
LOG_FILE="/home/synczus/kestrel/auto-git.log"

cd "$REPO_DIR" || exit 1

# Check if there are any changes
if git status --short | grep -q .; then
    # Build a summary of what changed
    SUMMARY=$(git status --short | awk '{print $NF}' | tr '\n' ' ' | head -c 200)
    
    git add -A
    git commit -m "auto: compound state — $(date '+%Y-%m-%d %H:%M') — ${SUMMARY}"
    git push origin main 2>> "$LOG_FILE"
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') — committed and pushed: ${SUMMARY}" >> "$LOG_FILE"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') — no changes" >> "$LOG_FILE"
fi