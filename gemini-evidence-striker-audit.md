# Gemini Evidence Packet — Striker Ground Truth Audit

**Date:** 2026-06-07 01:15 EDT  
**Cycle:** v3.2 — Stage 3 (Gemini)  
**Status:** ✅ Evidence mapped

---

## Verified Facts

### 1. striker_health.json
| Field | Value |
|-------|-------|
| status | `"stopped"` |
| connected_since | null |
| signals_this_session | 0 |
| total_signals | 0 |
| updated_at | `2026-06-07T02:55:38 UTC` |

**Interpretation:** Not running. Last health write ~15 min ago (likely from a systemd restart attempt that exited). No signals ever emitted.

### 2. kestrel_signals.db
- **Schema:** EXISTS — `signals` table with id, timestamp, symbol, price, direction, confidence, move_pct, volume
- **Index:** `idx_signals_ts` on (timestamp) — EXISTS
- **Row count:** **0** — no signals ever written

### 3. core/main.py (Current, Rebuilt)
- **Fully async WebSocket client** using `websockets` library
- **PriceTracker** class — seed first tick, then detect moves ≥ 0.5%
- **StrikerClient** — connect/reconnect loop with exponential backoff (1s → 30s cap)
- **SIGTERM/SIGINT handlers** wired via `loop.add_signal_handler`
- **Health tick** every 60s writing to striker_health.json
- **DB writes** on every signal (individual INSERT, no batch)
- **Logging** to stderr (stdout reserved for signal JSON)

**NOT the "neutered sleep(3600)" version** — this is the rebuilt production-grade client.

### 4. kestrel-striker.service (systemd Unit)
```
[Unit]
Description=Kestrel Striker
After=network-online.target
Wants=network-online.target

[Service]
User=synczus
Group=synczus
WorkingDirectory=/home/synczus/kestrel
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=/home/synczus/kestrel/.env
ExecStart=/home/synczus/kestrel/.venv/bin/python core/main.py
Restart=always
RestartSec=5
StartLimitIntervalSec=60
StartLimitBurst=5
TimeoutStopSec=10
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
```

### 5. Config
- **WS URL:** `wss://ws-feed.pro.coinbase.com` (set in .env)
- **Default in config.py:** `wss://advanced-trade-ws.coinbase.com` (overridden by .env)
- **Symbols:** BTC-USD, ETH-USD, SOL-USD
- **Threshold:** 0.5%
- **Queue max:** 1000

### 6. Directory Layout
```
kestrel/
├── core/
│   └── main.py          # Rebuilt async WS client (current)
│   └── config.py         # Env-based config loader
├── kestrel-striker.service  # systemd unit file
├── striker_health.json      # Health state (stopped, 0 signals)
├── kestrel_signals.db       # SQLite DB (0 rows)
├── .env                     # Credentials + config
├── .venv/                   # Python venv with dependencies
├── dashboard/               # Compound dashboard
├── creative-arsenal/        # Content weights
├── agent-pulses/            # Agent output archive
├── shared-skills/           # Protocol skills
├── memory-bank/             # Proposition archive
└── squirrel-inbox/          # File drop inbox
```

---

## Gaps / Unverified Claims

| Claim | Status | Evidence |
|-------|--------|----------|
| "WS endpoint is live" | ❌ Unverified | No test run since rebuild |
| "Reconnect works" | ❌ Unverified | backoff logic in code, never tested under systemd |
| "DB writes are atomic" | ⚠️ Partial | Individual INSERT per signal, no explicit transaction wrapping in write_signal() |
| "Service starts clean" | ❌ Unverified | Health shows "stopped" — service may be failing silently |
| "Health tick works" | ❌ Unverified | Code has 60s health tick but never ran long enough to verify |
| "No duplicate instances" | ❌ Unverified | No lock file, no PID file — Restart=always could spawn multiples |

---

## Issues Found

### 🔴 CRITICAL — Credential Exposure
**`.env` file contains TELEGRAM_BOT_TOKEN in plain text.** The token is visible and accessible to any process running as `synczus`. This should be moved to a secrets manager or at minimum `chmod 600`.

### 🟡 WARNING — WS URL Mismatch Risk
- **.env says:** `wss://ws-feed.pro.coinbase.com` (pro feed)
- **config.py default:** `wss://advanced-trade-ws.coinbase.com` (advanced trade)
- **Hop payload says:** `wss://advanced-trade-api-ws.coinbase.com`
- Three different URLs referenced. Need to verify which one actually works for the subscription format in main.py's `_subscribe` method (uses "ticker" channel with "product_ids" → this is the **Advanced Trade** format, not the pro feed).

### 🟡 WARNING — No Single-Instance Enforcement
No `flock`, PID file, or lock file. With `Restart=always` + `RestartSec=5` + `StartLimitBurst=5`, rapid restart storms could spawn multiple writers to the same DB and health file.

### 🟡 WARNING — No Health Endpoint
No `/health` endpoint or external health check interface. Kairos currently has nothing to monitor except file mtime on `striker_health.json`, which is stale (stopped).

### 🟢 GREEN — Code Quality
- Signal handling wired properly (SIGTERM/SIGINT)
- Exponential backoff implemented
- Structured logging to stderr, JSON to stdout
- Config loaded from env (12-factor compliant)
- Graceful shutdown in `finally` block

---

## Summary

Striker's `core/main.py` has already been rebuilt into a production-grade async WS client. The code is solid. The issues are in the **runtime layer**: systemd configuration, credential hygiene, single-instance enforcement, and monitoring integration. The service file exists but may be failing silently (health shows "stopped"). Need to test-start and observe behavior before declaring the daemon ready.

```
NEXT AGENT ROUTING:
Next Agent Name: Claude
Next Agent Role: Architect / Risk Judge
Reason for next hop: Gemini mapped the on-disk reality. Striker's main.py is already production-grade code. The risks are in the runtime layer (systemd config, credential hygiene, monitoring integration). Claude must judge which risks to fix now vs defer.
Instruction to next agent: Use this evidence packet to produce a risk-ranked assessment. Distinguish between (a) issues that will cause silent signal loss vs (b) hygiene that can wait. Define the do-not-touch list. Recommmend the safe edit sequence for the systemd unit and any code changes needed.
Context to pass forward: Cron fix closure (verified) + Striker evidence packet (health, DB, code, service file, config, directory layout) + verified gaps (no lock file, no health endpoint, credential exposure, WS URL ambiguity, 0 signals in DB) + open loops (Kairos monitoring, Telegram alerts, boot persistence across gateways).
```