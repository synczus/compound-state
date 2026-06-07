#!/usr/bin/env bash
# Auto-push — commits and pushes tracked changes.
# Silent if nothing to push. Respects .gitignore.
# Cron schedule: every 6h (set elsewhere)

set -euo pipefail

REPOS=(
  "/home/synczus/projects/active/huntsystems"
)

for REPO in "${REPOS[@]}"; do
  [ -d "$REPO/.git" ] || continue
  cd "$REPO"

  # Count what changed (tracked files only, respecting .gitignore)
  TRACKED=$(git diff --name-only 2>/dev/null | wc -l)
  UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l)
  BOTH=$((TRACKED + UNTRACKED))
  [ "$BOTH" -eq 0 ] && continue

  # Build a summary for the commit message
  BRANCH=$(git rev-parse --abbrev-ref HEAD)
  SUMMARY="auto: $(date -u '+%Y-%m-%d %H:%M UTC')"

  if [ "$TRACKED" -gt 0 ]; then
    SUMMARY="$SUMMARY | ${TRACKED} tracked changed"
  fi
  if [ "$UNTRACKED" -gt 0 ]; then
    SUMMARY="$SUMMARY | ${UNTRACKED} untracked added"
  fi

  # Stage and commit
  git add -A 2>/dev/null
  git commit -m "$SUMMARY" 2>/dev/null || true

  # Push silently
  git push origin "$BRANCH" -q 2>/dev/null || echo "[AUTO-PUSH] Push failed for $REPO ($BRANCH)" >&2
done