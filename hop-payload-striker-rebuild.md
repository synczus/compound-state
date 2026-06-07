# Hop Payload — v1.1 First Execution

```json
{
  "payload": {
    "deliverable": "Restore Kestrel Striker live signal engine — Coinbase websocket scanner that emits structured high-conviction signals with health monitoring and auto-reconnect",
    "success_criteria": [
      "Websocket reconnects on network loss within 5s (exponential backoff, no crash loop)",
      "Emits structured signal JSON with timestamp, symbol, price, direction, confidence",
      "Health endpoint at core/health.py returns status + signal count + connection state",
      "Signals get injected into the compound feed (broadcast to group or pulse file)",
      "systemd stabilizes within 3 restarts — no Restart=always thrash"
    ],
    "timebox_hours": 4,
    "priority": "P0"
  }
}
```

## Current State

- `core/main.py` — neutered: `while True: sleep(3600)`
- `core/config.py` — config exists for Coinbase WS, scan symbols ($BTC-USD, $ETH-USD, $SOL-USD), price threshold (0.5%)
- `kestrel_signals.db` — SQLite DB for signal storage (exists, format unknown, may need schema check)
- systemd service `kestrel-striker.service` — active, Restart=always, WorkingDirectory=/home/synczus/kestrel, runs `.venv/bin/python core/main.py`
- No git history — files are local only

## Lane Assignments

### codex-operator (Hermes)
Rebuild `core/main.py` with:
- Coinbase WebSocket client (wss://advanced-trade-api-ws.coinbase.com)
- Signal detection: price move > 0.5% threshold
- Structured signal output (JSON to stdout + optional DB write)
- Exponential backoff reconnection
- Graceful SIGTERM handling for systemd

### gemini-scout (evidence mapper)
- Verify Coinbase WS endpoint is still live/valid
- Check if signal DB schema exists and is compatible
- Verify the config file's symbol list and thresholds match actual Coinbase pairs

### claude-architect (risk judge)
- Review rebuild plan before write: reconnect strategy, resource cleanup, signal schema design, crash boundaries
- Ensure health monitor path doesn't block the main loop

### openclaw-tinkerer
- Verify systemd service can handle the new code (restart behavior, .env vars)
- Ensure Striker starts/stops cleanly with the new main.py

### kairos-daemon
- Define signal monitoring pattern: frequency check, stale-signal detection, alert path

## Output

Each lane produces:
1. Their work (code changes, findings, reviews)
2. A pulse to `kestrel/agent-pulses/2026-06-06/`
3. HLM appended to master-todo.md