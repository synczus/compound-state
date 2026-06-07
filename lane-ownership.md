# Lane Ownership & File Territory

Every file has one owner. If you need to change something in another agent's territory: propose it, tag the owner, wait for sign-off. No silent writes across lanes.

## Ownership Map

### OpenClaw — Config Lane
Owns:
- `~/.openclaw/openclaw.json` — gateway config
- `~/.openclaw/agents/*/agent/openclaw.json` — agent configs
- `~/.config/systemd/user/openclaw-*.service` — systemd units
- `~/.config/systemd/user/openclaw-*.service.d/env.conf` — env overrides
- `~/.openclaw/agents/main/agent/auth-profiles.json` — auth profiles
- `kestrel/tool-registry.json` (infrastructure section only)
- Systemd daemon-reload, enable, restart commands

### Nemoclaw — Identity Lane
Owns:
- `kestrel/swarm-briefing.md`
- `kestrel/lane-ownership.md` (this file)
- `kestrel/content-weights.md`
- `kestrel/identity/*.md` — all identity files
- `kestrel/clinical/*.md` — clinical docs
- `kestrel/skills/*/SKILL.md` — skill documentation
- `kestrel/skills/README.md` — skill catalog
- `~/.openclaw-nemo/.openclaw/workspace/SOUL.md` — Nemoclaws own SOUL
- `~/.hermes/profiles/kairos/SOUL.md` — Kairos SOUL (identity content)
- `~/.hermes/profiles/shannon/SOUL.md` — Shannon SOUL (identity content)
- `kestrel/hop-protocol-*.md` — protocol specs
- `kestrel/initiation-protocol.md`
- `memory/*.md` — daily memory files

### Hermes — Cron/Execution Lane
Owns:
- `kestrel/master-todo.md` — sprint board (append only, do not restructure)
- `kestrel/agent-pulses/*/` — pulse archive
- `kestrel/skills/autonomous-chat/scripts/*.sh` — pulse scripts
- `kestrel/skills/autonomous-chat/constraints.json` — constraint engine
- `kestrel/skills/market-pulse/scripts/*` — market scripts
- `kestrel/skills/pipeline-signal/scripts/*` — bridge scripts
- `kestrel/dialogue-state.json`
- `kestrel/HUB_INTAKE.md`
- `kestrel/memory-bank/*` — archive squirrel territory
- `kestrel/inbox/` — file archiver output
- Crontab entries

### Kairos — Timing/Ops Lane
Owns:
- Health check scripts and configs
- Security audit notes
- Timing/cadence decisions
- Port/service scan outputs
- `kestrel/tool-registry.json` — owns the monitoring/health sections
- Gateway health verifications
- Pipeline cadence definitions

### Shannon — Referee Lane
Owns:
- CTF scoring rules and leaderboard data
- Arbitration rulings (written to `kestrel/identity/arbitration-log.md`)
- Code review verdicts
- Signal/noise classifications on pipeline output
- Contest results and scoring

**Does NOT own any executable files or config files.** Shannon is a reviewer, not a writer — Shannon can propose changes to any lane's files but must tag the owner for approval.

## Cross-Lane Write Protocol

1. **Silent write forbidden.** If you are not the listed owner of a file, do not edit it without announcing in group first.
2. **Tag the owner.** Before editing: "@OwnerName I need to change X because Y. Approve?"
3. **Owner has 5 minutes to respond.** If no response, the change is assumed safe.
4. **After edit, notify.** "Updated X per our conversation."
5. **Rollback rule.** If the owner says "revert that," the change is undone within 5 minutes. No arguments.

## Exception: Group Coordination Files

These files are **append-only** and any agent can write to them:
- `kestrel/master-todo.md` — append new tasks or HLMs. Do not restructure or delete other agents' entries.
- `kestrel/agent-pulses/YYYY-MM-DD/pulse-*.md` — append new pulses. Do not edit existing pulses.
- `kestrel/inbox/YYYY-MM-DD/*` — file archiver output. Write only.

## File Touch Rules

| Action | Rule |
|---|---|
| Read any file | Always allowed |
| Write your owned files | Always allowed |
| Propose cross-lane change | Tag owner in group, wait 5 min |
| Delete any file | Tag owner in group, wait for explicit approval |
| Restructure/rename files | Tag owner in group, wait for explicit approval |
| Append to shared board | Always allowed (append only, do not modify existing entries) |

## Verification

Every agent should read this file on session startup alongside the swarm briefing and tool registry. If there is a conflict between two agents claiming the same file, escalate to Chase.