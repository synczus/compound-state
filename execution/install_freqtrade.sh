#!/usr/bin/env bash
# install_freqtrade.sh — Install Freqtrade + set up execution layer
# Run: bash execution/install_freqtrade.sh

set -euo pipefail

KESTREL_HOME="$HOME/kestrel"
FREQTRADE_DIR="$KESTREL_HOME/execution/freqtrade"

echo "==> Installing Freqtrade on Ubuntu 22.04..."

# ── Python 3.11 + venv ──
if ! python3.11 --version &>/dev/null; then
    echo "Installing Python 3.11..."
    sudo apt update && sudo apt install -y python3.11 python3.11-venv python3.11-dev build-essential git
fi

# ── Virtual env ──
if [ ! -d "$KESTREL_HOME/execution/freqtrade_env" ]; then
    echo "Creating virtualenv..."
    python3.11 -m venv "$KESTREL_HOME/execution/freqtrade_env"
fi

# ── Install Freqtrade ──
echo "Installing freqtrade + dependencies..."
source "$KESTREL_HOME/execution/freqtrade_env/bin/activate"
pip install --upgrade pip
pip install freqtrade duckdb pandas
deactivate

# ── Create state directories ──
mkdir -p "$FREQTRADE_DIR/strategies"
mkdir -p "$FREQTRADE_DIR/logs"
mkdir -p "$FREQTRADE_DIR/user_data"
mkdir -p "$KESTREL_HOME/execution/state"
mkdir -p "$KESTREL_HOME/logs/cron"

# ── Config exists check ──
if [ -f "$FREQTRADE_DIR/config.json" ]; then
    echo "✔ Config found at $FREQTRADE_DIR/config.json"
    echo "  ⚠ Edit the exchange key/secret fields before running live"
    echo "  config.json exchange.key = YOUR_CB_API_KEY"
    echo "  config.json exchange.secret = YOUR_CB_API_SECRET"
fi

# ── Verify ──
echo ""
echo "==> Verification:"
source "$KESTREL_HOME/execution/freqtrade_env/bin/activate"
freqtrade --version 2>/dev/null && echo "✔ freqtrade installed" || echo "✗ freqtrade not found"
python3 -c "import duckdb; print('✔ duckdb importable')" 2>/dev/null || echo "✗ duckdb not importable"
deactivate

echo ""
echo "==> DONE. Next steps:"
echo "  1. Add your Coinbase Advanced Trade API credentials to:"
echo "     $FREQTRADE_DIR/config.json"
echo "  2. Test in dry-run mode:"
echo "     cd $FREQTRADE_DIR"
echo "     source ../freqtrade_env/bin/activate"
echo "     freqtrade trade --config config.json --strategy DuckDBSignalStrategy"
echo "  3. Run the dual supervisor to verify pipeline bridge:"
echo "     cd $KESTREL_HOME"
echo "     python3 execution/dual_supervisor.py"