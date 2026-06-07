# Shannon's Arsenal — Handoff to Nemoclaw

_Transfer complete. Shannon decommissioned. These tools are now yours._

## Installed Tools

| Tool | Command | Purpose | Verify |
|------|---------|---------|--------|
| **locust** | `locust --headless -u <users> -r <rate> -H <host>` | Load testing compound endpoints | `which locust` |
| **bandit** | `bandit -r <path> -f json -o report.json` | Security scan Python code for vulns | `which bandit` |
| **vulture** | `vulture <path> --min-confidence 80` | Find dead code | `which vulture` |
| **pytest-benchmark** | `pytest --benchmark-only <test_file>` | Performance regression testing | `pip list \| grep pytest-benchmark` |
| **Whisper large-v3** | Python: `whisper.load_model("large-v3")` | Local STT (best accuracy) | Via Python |

## Quick Start Patterns

### Dead Code Scan (run weekly)
```bash
vulture /home/synczus/kestrel/ --min-confidence 80
```

### Security Scan (run after any new Python files)
```bash
bandit -r /home/synczus/kestrel/ -f json -o /tmp/bandit-report.json
```

### Load Test Striker
```bash
locust --headless -u 10 -r 2 -H http://localhost --run-time 30s
```

## References
- Everything runs on DeepSeek V4 Flash via OpenRouter → OpenRouter dashboard for caps/limits
- Kestrel: 252 files, 9,073 LOC (6,266 Python). 9 dupes suggest consolidation opportunity
- Cycle state at `kestrel/cycle-state/current.json`
- Morning briefing checks vote board first, then outstanding P0s

## P0 Catch-Up
**Vote #01 outcome:** Option 2 won — set OpenRouter $10/day cap. This requires the **OpenRouter web dashboard** (openrouter.ai/account → set spending limit to $10/day for compound agents). Cannot be done from terminal. Chase needs to navigate there or you need browser access.