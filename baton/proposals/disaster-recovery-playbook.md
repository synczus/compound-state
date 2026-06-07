# Disaster Recovery Playbook

**Status:** Design Proposal | **Owner:** Fleet | **Priority:** P2

## Problem

Everything lives on one machine (ubuntu). No backup. No deploy-from-scratch.
No recovery playbook. If the server dies, the entire compound dies with it.

## Design

### Tier 1: Config Backup (Tonight)

Daily tar of essential configs → GitHub:
```
/home/synczus/kestrel/
/home/synczus/.config/systemd/user/*.service
```
Just add these paths to the auto-git-sync cron.

### Tier 2: Bootstrap Script

Write `/home/synczus/kestrel/scripts/recover.sh`:
```
#!/bin/bash
# Recover Kestrel compound from scratch
# 1. Clone repos
# 2. Install python deps (.venv)
# 3. Copy systemd user services
# 4. Enable + start all services
# 5. Validate (ping each port)
```

### Tier 3: Offsite (Future)

- DB dumps to cloud storage
- Agent session logs archived off-machine
- Recovery drill (test the script on a fresh VM)

## Success Criteria

- Running `recover.sh` on a fresh Ubuntu install brings the full compound online
- No manual steps required beyond `git clone` + `bash recover.sh`