#!/usr/bin/env bash
# Hermes Bridge / Health Check — every 30 min
# SILENT: Only posts to AI Hangout if something is broken or degraded.
set -euo pipefail

CHAT_ID="-5087043705"
BOT_TOKEN="8692705040:AAGswwTzlBFBjR3CUWWfYqQ4MIzWwqLx_KQ"
LOG="/home/synczus/kestrel/logs/hermes-health.log"

check_service() {
    local name=$1 svc=$2
    local status
    status=$(systemctl is-active "$svc" 2>/dev/null || echo "inactive")
    if [ "$status" != "active" ]; then
        echo "🔴 $name ($svc) is $status"
    fi
}

issues=""

# Gateways
issues+=$(check_service "OpenClaw (18789)" "openclaw-gateway.service" || true)
issues+=$(check_service "OpenClaw (18791)" "openclaw-2.service" || true)
issues+=$(check_service "Striker" "kestrel-striker.service" || true)
issues+=$(check_service "MiroFish" "kestrel-mirofish-synczus.service" || true)
issues+=$(check_service "Ollama" "ollama.service" || true)
issues+=$(check_service "Headroom" "headroom-proxy.service" 2>/dev/null && true || true)

# Check headroom as user service
headroom_ok=$(systemctl --user is-active headroom-proxy.service 2>/dev/null || echo "inactive")
if [ "$headroom_ok" != "active" ]; then
    issues+="🔴 Headroom proxy is $headroom_ok"$'\n'
fi

# Check ports
for port_desc in "OpenClaw 18789" "OpenClaw2 18791" "MiroFish 8000" "Headroom 8787"; do
    port=$(echo "$port_desc" | awk '{print $2}')
    name=$(echo "$port_desc" | awk '{print $1}')
    if ! ss -tlnp | grep -q ":$port "; then
        issues+="🔴 Port $port ($name) not listening"$'\n'
    fi
done

# Check disk
disk_used=$(df / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$disk_used" -gt 85 ]; then
    issues+="🟡 Disk at ${disk_used}%"$'\n'
fi

# Check Striker DB freshness
if [ -f /home/synczus/kestrel/kestrel_state.db ]; then
    db_age=$(( $(date +%s) - $(stat -c %Y /home/synczus/kestrel/kestrel_state.db) ))
    if [ "$db_age" -gt 3600 ]; then
        issues+="🟡 Striker state DB not updated in $(( db_age / 60 ))m"$'\n'
    fi
fi

if [ -n "$issues" ]; then
    msg="🛡️ *Hermes Health Check*\n$(date '+%H:%M')\n\n$issues"
    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d "chat_id=${CHAT_ID}" \
        -d "text=${msg}" \
        -d "parse_mode=Markdown" \
        -o /dev/null
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) ALERT: posted health issues" >> "$LOG"
else
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) OK" >> "$LOG"
fi