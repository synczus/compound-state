#!/bin/bash
# health-check.sh — Validate all compound services + configs
# Silent when healthy, outputs issues when found

FAILURES=0

check_service() {
    name=$1
    systemctl --user is-active "$name" &>/dev/null && return 0
    echo "🔴 $name — INACTIVE"
    return 1
}

check_url() {
    name=$1
    url=$2
    code=$(curl -sf -o /dev/null -w "%{http_code}" --max-time 3 "$url" 2>/dev/null || echo "000")
    if [ "$code" = "000" ]; then
        echo "🔴 $name ($url) — unreachable"
        return 1
    fi
    if [ "$code" != "200" ] && [ "$code" != "404" ]; then
        echo "⚠️  $name ($url) — HTTP $code"
    fi
    return 0
}

check_git_remote() {
    dir=$1
    name=$2
    cd "$dir" 2>/dev/null || { echo "🔴 $name — directory missing"; FAILURES=$((FAILURES+1)); return; }
    if ! git remote -v &>/dev/null; then
        echo "🔴 $name — no git remote"
        FAILURES=$((FAILURES+1))
    fi
}

check_env_perms() {
    file=$1
    name=$2
    if [ -f "$file" ]; then
        perms=$(stat -c "%a" "$file")
        if [ "$perms" != "600" ]; then
            echo "⚠️  $name ($file) — permissions $perms, should be 600"
            FAILURES=$((FAILURES+1))
        fi
    fi
}

# Services
for s in kestrel-striker hermes-gateway kairos-gateway shannon-gateway; do
    check_service "$s" || FAILURES=$((FAILURES+1))
done

# URLs
check_url "WolfWatch" "http://127.0.0.1:18790/notify"
check_url "Paperclip" "http://127.0.0.1:3100/"
check_url "Kestrel API" "http://127.0.0.1:8000/api/v1/health"
check_url "Archive Squirrel" "http://127.0.0.1:8766/health"

# Git repos
check_git_remote "/home/synczus/archivesquirrel" "archivesquirrel"
check_git_remote "/home/synczus/kestrel" "compound-state"

# Security
check_env_perms "/home/synczus/.hermes/.env" "hermes .env"

# Logs
log_count=$(find /home/synczus/huntsystems/logs/cron/ -name "*.log" | wc -l)
echo "📊 Cron logs: $log_count files in crons/"

if [ "$FAILURES" -eq 0 ]; then
    echo "✅ All checks passed"
else
    echo "❌ $FAILURES failure(s) found"
fi
exit $FAILURES
# ── Concept Drift Check ──
# Compare actual recent behavior vs SOUL.md stated principles
SOUL="/home/synczus/.openclaw/workspace/SOUL.md"
if [ -f "$SOUL" ]; then
    CORE_VALUES=$(grep -c "Be genuinely\|Have opinions\|Be resourceful\|Earn trust\|Remember you're a guest\|Private things stay" "$SOUL" 2>/dev/null || echo 0)
    if [ "$CORE_VALUES" -lt 3 ]; then
        echo "⚠️  Concept drift suspected — SOUL.md core principles may be stale ($CORE_VALUES found)"
        FAILURES=$((FAILURES+1))
    fi
fi
