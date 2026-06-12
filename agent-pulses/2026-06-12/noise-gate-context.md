# Noise Gate Context

_Generated: 2026-06-12 15:53:40 UTC_

## Last 24h

- PROMOTE: 73
- PURGE: 93
- Total: 166

## Top Reasons

- No significant markers found: 93
- Security/vulnerability signal: 54
- Dependency/ecosystem shift: 23
- Direct actionability detected: 8
- Structural shift (engineering refactor/rewrite): 6
- Convergence detected: 5
- Asymmetry/Contrarian signal detected: 2

## Sources

- GitHub_vscode: 69
- GitHub_unsloth: 62
- GitHub_llama.cpp: 16
- GitHub_langchain: 9
- GitHub_ComfyUI: 6
- GitHub_ollama: 3
- GitHub_openai-python: 1

## Recent Decisions

- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit ab7eee2 by Benjamin Christopher Simmonds: Add best practices instructions file (#321160)  * Add best practices in
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit be93ed6 by Megan Rogge: Fix Space key activating header buttons instead of PTT in voice mode (#321164)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 46171a9 by Paul: Add isBYOK signal to distinguish CAPI vs BYOK models (#321090)  * Add isBYOK signal to distingui
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit b91116c by Daniel Han: studio: declare UNSLOTH_IS_PRESENT at backend startup (#6262)  The studio backend lazily i
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit c1d6f5b by Megan Rogge: Fix Copilot terminal profile resolution when shell doesn't exist (#321154)  When the reso
- PURGE score=0 source=GitHub_unsloth reason=No significant markers found preview=Commit 5300c04 by oobabooga: Installer: drop the lemonade ROCm fallback now the fork ships identical per-gfx prebuilts (
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit cc32777 by sqersters: Studio: keep distinct bpw flavors of the same GGUF quant (#5729)  list_gguf_variants() keys
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 55d4342 by Connor Peet: agents: add exp settings for default agent selection (#320896)  * agents: add exp setting
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit e6455d8 by Sandeep Somavarapu: sessions: track preferred session type when no explicit user pick (#321141)  * ses
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit 02656ea by comfyanonymous: Fix potential dtype issue with ideogram 4. (#14436)
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit d7a5527 by rattus: add --high-ram option (#14437)  Add this option for users who know they have so much ram they 
- PROMOTE score=3 source=GitHub_llama.cpp reason=Dependency/ecosystem shift preview=Commit ebc1077 by Georgi Gerganov: server : fix reasoning budget WebUI precedence over model.ini (#24517)  When reasonin

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
