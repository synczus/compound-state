---
name: stress-testing-skill
category: devops
tags: [stress, load, testing, system, performance]
description: Stress test and optimize system resources, pipeline performance, and agent resilience under load.
---

# Stress Testing & Optimization Toolkit

Skill for compound agents to stress test and optimize the environment. Agent-agnostic — any agent managing pipeline health, code quality, or system resilience can use this.

## Installation

```bash
# Already installed:
k6        - /home/synczus/.local/bin/k6 (load testing, v0.57.0)
perf      - CPU profiling, performance counters
iostat    - I/O monitoring
htop      - System resource monitor
vmstat    - Process/memory/paging stats
ss        - Socket statistics
lsof      - Open file descriptors
tcpdump   - Network packet capture
curl/wget - HTTP testing

# Not installed (needs sudo):
stress-ng - CPU/memory/disk/system stress
ab        - Apache Bench (HTTP benchmarking)
sysbench  - CPU/memory/thread stress
```

## Quick Commands

### CPU Stress Test
```bash
# Max CPU pressure for 60s
perf stat -a -- sleep 60 &
# Monitor utilization
htop
```

### Memory Test
```bash
# Check memory pressure
vmstat 1 10
# Check OOM score
cat /proc/*/oom_score | sort -rn | head -10
```

### Disk I/O Test
```bash
# Monitor I/O
iostat -x 1 10
```

### Network Test
```bash
# Check connections
ss -tunap
```

### Load Testing (k6)
```bash
k6 run --vus 10 --duration 30s -e TARGET=http://localhost:3100 -
```
k6 scripts in `/home/synczus/kestrel/scripts/load-tests/`

## Scripts

| Script | Path | Purpose |
|--------|------|---------|
| Stress Test Suite | `/home/synczus/kestrel/scripts/stress-test.sh` | Run system under pressure, measure effect |
| System Audit | `/home/synczus/kestrel/scripts/system-audit.sh` | Comprehensive system snapshot |
| k6 Load Test | `/home/synczus/kestrel/scripts/load-tests/paperclip-api.js` | Paperclip API performance test |
| Backtrader Bridge | `/home/synczus/kestrel/scripts/striker-backtrader-bridge.py` | Backtest Striker signals against historical data |
| Freqtrade Bridge | `/home/synczus/kestrel/freqtrade/` | Live paper-trading with Striker signals |
| Inversion Cron | `/home/synczus/kestrel/scripts/inversion-cron.sh` | 10-min stress test of active work items (see Inversion Cron section) |
| Perplexity Search | `/home/synczus/kestrel/scripts/perplexity_search.py` | Inline web-grounded research via OpenRouter (see `references/perplexity-inline-research.md`) |

## Agent Workflows

### Stress Test Loop
```bash
./stress-test.sh all 30         # baseline
k6 run load-tests/paperclip-api.js  # apply load
./stress-test.sh all 30         # under load
./system-audit.sh               # full snapshot
```

### n8n Stress Test

n8n community edition runs on port 5678. Test methodology:

```bash
# 1. Health check (no auth needed)
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5678/healthz
# Expected: 200

# 2. Settings endpoint (no auth needed for read)
curl -s http://127.0.0.1:5678/rest/settings | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('userManagement',{}))"
# Shows auth method, setup state

# 3. Webhook endpoint test (n8n creates webhook URLs like /webhook/<id>)
# Create a test workflow first via the UI, then:
for i in 1 2 3 4 5; do
  time curl -s -X POST http://127.0.0.1:5678/webhook/test-webhook \
    -H "Content-Type: application/json" \
    -d '{"test": true}' -o /dev/null -w "%{http_code} %{time_total}s\n"
done

# 4. API key auth test (returns 401 until owner account created)
curl -s http://127.0.0.1:5678/rest/workflows \
  -H "X-N8N-API-KEY: <key>" | python3 -m json.tool
# Expected until owner setup: {"status":"error","message":"Unauthorized"}

# 5. Docker volume persistence check
docker inspect n8n --format '{{json .Mounts}}'
# Empty array [] = no persistent volume = data lost on restart
# Fix: stop container, restart with -v /home/synczus/n8n-data:/home/node/.n8n
```

Key findings from testing:
- n8n is accessible without auth on /healthz and /rest/settings
- API key auth requires an owner account to be created via the signup flow at http://localhost:5678/signup
- Without persistent Docker volume, all users/workflows/credentials are lost on container restart
- The community edition has no execution limits — full local engine

### Signal Pipeline Backtest
```bash
cd /home/synczus/kestrel
python3 scripts/striker-backtrader-bridge.py
```
Tests three assets (SOL, ETH, BTC) against 2-hour windows of Striker signal data.

### Freqtrade Dry-Run Stress
```bash
# Check if freqtrade API is live
curl -s http://127.0.0.1:8081/api/v1/ping
# Check open trades
curl -s http://127.0.0.1:8081/api/v1/status
```

### System Health Check
Monitor: cpu load, memory pressure, OOM scores, swap usage, disk I/O wait, network socket count.

### Bottleneck Detection
- **High CPU** → `perf top`, check which process, review OOM limits
- **High I/O wait** → `iostat -x 1`, identify noisy processes
- **High memory** → `ps aux --sort=-%mem | head`, check OOM scores
- **Socket limits** → `ss -s`, `/proc/sys/net/core/somaxconn`
- **API slow** → `k6 run` with increasing VUs until p95 degrades

### Inversion Cron: Automated Assault Testing

**Pattern:** Every 10 minutes, a cron job reads the active work item, calls Perplexity to attack its assumptions, and writes a pulse. This pressure-tests the compound's current direction without human intervention.

#### Setup

```bash
# 1. Create the inversion cron script
cat > /home/synczus/kestrel/scripts/inversion-cron.sh << 'EOF'
#!/bin/bash
HOP_FILE="/home/synczus/kestrel/cycle-state/hop-sequence.json"
SCRIPT="/home/synczus/kestrel/scripts/perplexity_search.py"
PULSES="/home/synczus/kestrel/agent-pulses/$(date +%Y-%m-%d)"
mkdir -p "$PULSES"
QUERY=$(python3 -c "import json; h=json.load(open('$HOP_FILE')); print(h.get('query','No active work item'))")
INVERSION=$(python3 "$SCRIPT" "Inversion analysis: The compound is working on '$QUERY'. Attack every assumption. What's wrong? What's overlooked? What should they do instead?")
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "$TIMESTAMP | inversion-cron | $INVERSION" >> "$PULSES/inversion-pulse.md"
echo "Inversion complete"
EOF
chmod +x /home/synczus/kestrel/scripts/inversion-cron.sh

# 2. Add to crontab (every 10 min)
(crontab -l 2>/dev/null; echo "*/10 * * * * cd /home/synczus/kestrel && bash scripts/inversion-cron.sh >> logs/inversion-cron.log 2>&1") | crontab -

# 3. Verify
crontab -l | grep inversion
```

#### How It Works

1. **Cron fires** every 10 minutes
2. **Script reads** `hop-sequence.json` to get the active query
3. **Calls Perplexity** via `scripts/perplexity_search.py` with an inversion prompt: "Attack every assumption. What's wrong? What's overlooked?"
4. **Writes pulse** to `agent-pulses/<date>/inversion-pulse.md` with timestamp and full analysis
5. **Pulse bridge** picks it up and routes to the group every 15 min

#### Inversion Prompt Template

```
"Inversion analysis: The compound is currently working on this: '{active_query}'. Attack every assumption. What's wrong with this plan? What's being overlooked? What should they be doing instead? Be blunt."
```

#### Cost

~$0.002 per call (Perplexity Sonar Pro via OpenRouter). ~$0.29/day at 10-min intervals.

#### Pitfalls

- **Stale hop state** — If the hop-sequence.json query field isn't updated, the inversion attacks an irrelevant target. Keep the hop baton current.
- **Noise at night** — If no agents are working, the inversion gets boring. Optional: skip if `active: false` in hop state.
- **Perplexity API limits** — At 10-min intervals, that's 144 calls/day. Monitor for 429s.
- **Inversion fatigue** — If every cycle produces the same critique, the pattern IS working — agents just need to resolve the underlying issue.
- **No retry** — The cron script doesn't retry on timeout. Wrap in a simple retry loop for production.
- **See also:** `references/perplexity-inline-research.md` for full Perplexity integration details.

## Scoring Rules

When scoring a stress test round:
1. **Baseline**: Measure CPU, memory, I/O, latency before load
2. **Load**: Apply stress, re-measure
3. **Recovery**: Time until metrics return to baseline after load stops
4. **Degradation**: How much metrics changed under load (lower = better)
5. **Score**: (Baseline threshold hits) / (Under load hits) × 100