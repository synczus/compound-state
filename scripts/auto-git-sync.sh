#!/usr/bin/env bash
# Auto-sync: commits local changes and pushes via SSH
# Cron-safe: only runs if there are changes, exits cleanly on remote mismatch

set -euo pipefail

SYNC_DIRS=(
  "/home/synczus/kestrel:origin/main"
  "/home/synczus/projects/active/huntsystems:origin/main"
)

for ENTRY in "${SYNC_DIRS[@]}"; do
  DIR="${ENTRY%%:*}"
  REMOTE_BRANCH="${ENTRY##*:}"

  cd "$DIR" || { echo "SKIP $DIR: not found"; continue; }

  # Skip if not a git repo
  git rev-parse --git-dir >/dev/null 2>&1 || { echo "SKIP $DIR: no git repo"; continue; }

  # Check if remote exists
  REMOTE="${REMOTE_BRANCH%%/*}"
  git remote get-url "$REMOTE" >/dev/null 2>&1 || { echo "SKIP $DIR: no remote '$REMOTE'"; continue; }

  # Check for changes
  CHANGES=$(git status --porcelain 2>/dev/null | wc -l)
  if [ "$CHANGES" -eq 0 ]; then
    echo "OK $DIR: clean"
    continue
  fi

  # Commit and push
  TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M UTC")
  git add -A
  git commit -m "auto: $TIMESTAMP" --no-gpg-sign --quiet 2>/dev/null || true
  
  if git push "$REMOTE" 2>&1; then
    echo "PUSH $DIR: $CHANGES changes pushed at $TIMESTAMP"
  else
    echo "SKIP $DIR: push failed (no matching remote or conflicting history)"
  fi
done
