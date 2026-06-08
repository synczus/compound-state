#!/usr/bin/env bash
set -e
VENV=/home/synczus/kestrel/venv
source "$VENV/bin/activate"

echo "[PIPELINE] $(date '+%H:%M:%S') Starting..."
cd /home/synczus/kestrel

python3 scripts/trade-extractor.py 2>&1
python3 scripts/multi-tf-analyzer.py --pending 2>&1
python3 scripts/signal-filter.py --threshold 0.25 2>&1

echo "[PIPELINE] $(date '+%H:%M:%S') Complete"
