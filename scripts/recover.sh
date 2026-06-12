#!/bin/bash
# Recover.sh — Bootstrap Kestrel Compound from Scratch
# Run this on a fresh Ubuntu install to restore the full compound
# Usage: bash recover.sh [github_user]
# Requires: git, python3, systemd (user mode)
set -euo pipefail

GH_USER="${1:-synczus}"
REPOS=("compound-state" "huntsystems")
LOG="/tmp/kestrel-recover.log"

echo "=== Kestrel Compound Recovery ===" | tee -a "$LOG"
echo "User: $GH_USER, Date: $(date)" | tee -a "$LOG"

# 1. Clone repos
mkdir -p ~/kestrel ~/projects/active
for REPO in "${REPOS[@]}"; do
    echo "Cloning $REPO..." | tee -a "$LOG"
    git clone "git@github.com:${GH_USER}/${REPO}.git" ~/kestrel 2>&1 | tee -a "$LOG"
done

# 2. Python venv
cd ~/kestrel
if [ ! -d .venv ]; then
    echo "Creating venv..." | tee -a "$LOG"
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --quiet -r requirements.txt 2>/dev/null || echo "No requirements.txt — skipping pip install" | tee -a "$LOG"

# 3. Systemd user services
mkdir -p ~/.config/systemd/user
for svc in ~/kestrel/*.service; do
    if [ -f "$svc" ]; then
        cp "$svc" ~/.config/systemd/user/
        echo "Installed service: $(basename $svc)" | tee -a "$LOG"
    fi
done
systemctl --user daemon-reload

# 4. Enable and start all services
echo "Enabling services..." | tee -a "$LOG"
for svc in ~/.config/systemd/user/kestrel-*.service; do
    name=$(basename "$svc")
    systemctl --user enable --now "$name" 2>&1 | tee -a "$LOG"
done

# 5. Make scripts executable
chmod +x ~/kestrel/scripts/*.sh ~/kestrel/scripts/*.py 2>/dev/null || true

# 6. Verify
echo "" | tee -a "$LOG"
echo "=== Verification ===" | tee -a "$LOG"
systemctl --user list-units --type=service --state=running | grep kestrel | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo "✅ Recovery complete. Full compound should be operational." | tee -a "$LOG"
echo "Check: systemctl --user status kestrel-striker.service" | tee -a "$LOG"