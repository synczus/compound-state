# Noise Gate Context

_Generated: 2026-06-13 15:09:43 UTC_

## Last 24h

- PROMOTE: 53
- PURGE: 57
- Total: 110

## Top Reasons

- No significant markers found: 57
- Security/vulnerability signal: 32
- Dependency/ecosystem shift: 19
- Structural shift (engineering refactor/rewrite): 8
- Direct actionability detected: 8
- Convergence detected: 3

## Sources

- GitHub_vscode: 48
- GitHub_unsloth: 23
- GitHub_langchain: 22
- GitHub_llama.cpp: 11
- GitHub_ComfyUI: 6

## Recent Decisions

- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit 341babc by Sigbjørn Skjæret: jinja : fix split and replace with empty first arg (#24574)  * fix split and replace
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit e8067a8 by Xuan-Son Nguyen: ui: build-time gzip compression (#24571)  * ui: keep original file name and path  * f
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit b664349 by Robin Huang: Expose deploy_environment in /system_stats (#14402)
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit 1a7718b by Jeff Bolz: vulkan: support non-contig unary/glu ops (#24215)  * vulkan: support non-contig unary/glu o
- PROMOTE score=5 source=GitHub_vscode reason=Direct actionability detected preview=Commit 275e1b3 by Alexandru Dima: build: add diagnostics to Copilot VSIX download poller (#321268)  The background `down
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit fe54b5e by Alexander Piskun: Add 10-bit video support (#14452)  Create Video gets a bit_depth option (8-bit/10-bi
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit 597b667 by Xuan-Son Nguyen: ui: keep original file name and path (#24568)  * ui: keep original file name and path
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit ed8f8bd by Alexandru Dima: Fix chat input selection rendering in Agents window (#320913)  * Fix chat input editor
- PURGE score=0 source=GitHub_unsloth reason=No significant markers found preview=Commit b32ef2e by Daniel Han: Bug fixes
- PROMOTE score=3 source=GitHub_unsloth reason=Dependency/ecosystem shift preview=Commit 8febe2c by Daniel Han: Bump install.sh / install.ps1 pin to unsloth>=2026.6.7 (#6301)
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit a9a38da by Daniel Han: Studio: decide diffusion routing before the SWA resolver (#6299)  * Studio: decide diffusi
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 55b6fb0 by Alexandru Dima: Prevent symbol tool file paths from escaping the working directory (#321259)  `Working

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
