# Compound Gauntlet — Stress Testing & Optimization

Skills for Shannon, Kairos, and all compound agents to stress test, profile, and harden the environment.

## Available Tools

### Load Testing (locust)
```bash
# Basic load test against a compound endpoint
locust --headless --users 10 --spawn-rate 1 -H http://127.0.0.1:8000 -t 30s
```
Use to find throughput bottlenecks, connection limits, timeout thresholds.

### Security Scanning (bandit)
```bash
# Scan a Python file or directory for security issues
bandit -r /path/to/code -f json -o /tmp/bandit-report.json
```
Flags: hardcoded passwords, eval(), SQL injection, unsafe YAML loading.

### Dead Code Detection (vulture)
```bash
# Find unused code
vulture /home/synczus/kestrel/scripts/ /home/synczus/kestrel/dashboard/ --min-confidence 70
```

### Performance Benchmarking (pytest-benchmark)
```bash
# Run benchmarks on critical compound functions
cd /home/synczus/kestrel && python -m pytest scripts/ --benchmark-only --benchmark-min-time=0.1
```

## The Gauntlet — Automated Stress Protocol

Run when a gauntlet round is declared:

1. **Service pulse** — `curl -sf -o /dev/null -w "%{http_code}"` each compound endpoint
2. **Resource check** — check CPU/mem/disk via `ps` and `df`
3. **Load spike** — start locust for 15s to test response degradation
4. **Security sweep** — run bandit on recently modified files
5. **Dead code sweep** — run vulture on scripts/
6. **Report** — post findings and score to the group

## Compound Endpoints to Stress

| Service | Port | Protocol |
|---|---|---|
| Kestrel API | 8000 | HTTP |
| Dashboard | 19500 | HTTP |
| ArchiveSquirrel | 8766 | HTTP |
| OpenClaw (kestrel) | 18789 | HTTP |
| OpenClaw (nemoclaw) | 18791 | HTTP |
| Striker | (systemd) | journald |

## Scoring (for The Gauntlet game)

| Find | Points |
|---|---|
| Dead service | 3 |
| Security vuln (critical) | 5 |
| Security vuln (medium) | 2 |
| Performance bottleneck | 3 |
| Dead code found | 1 |
| Config misconfig | 2 |
| Cron failure | 1 |
