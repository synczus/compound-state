# Stress Testing & Optimization Toolkit

Skill for Shannon and compound agents to stress test and optimize the environment.

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

## Agent Workflows

##n", "newText": "## Scripts

| Script | Path | Purpose |
|--------|------|---------|
| Stress Test Suite | `/home/synczus/kestrel/scripts/stress-test.sh` | Run system under pressure, measure effect |
| System Audit | `/home/synczus/kestrel/scripts/system-audit.sh` | Comprehensive system snapshot |
| k6 Load Test | `/home/synczus/kestrel/scripts/load-tests/paperclip-api.js` | Paperclip API performance test |

## Agent Workflows

### Stress Test Loop
```
./stress-test.sh all 30         # baseline
k6 run load-tests/paperclip-api.js  # apply load
./stress-test.sh all 30         # under load
./system-audit.sh               # full snapshot
```

### System Health Check
Monitor: cpu load, memory pressure, OOM scores, swap usage, disk I/O wait, network socket count

### Bottleneck Detection
- **High CPU** → `perf top`, check which process, review OOM limits
- **High I/O wait** → `iostat -x 1`, identify noisy processes
- **High memory** → `ps aux --sort=-%mem | head`, check OOM scores
- **Socket limits** → `ss -s`, `/proc/sys/net/core/somaxconn`
- **API slow** → `k6 run` with increasing VUs until p95 degrades

## Scoring Rules (for Shannon the Referee)

When scoring a stress test round:
1. **Baseline**: Measure CPU, memory, I/O, latency before load
2. **Load**: Apply stress, re-measure
3. **Recovery**: Time until metrics return to baseline after load stops
4. **Degradation**: How much metrics changed under load (lower = better)
5. **Score**: (Baseline threshold hits) / (Under load hits) × 100"}]