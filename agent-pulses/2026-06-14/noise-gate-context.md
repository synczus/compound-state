# Noise Gate Context

_Generated: 2026-06-14 01:43:45 UTC_

## Last 24h

- PROMOTE: 24
- PURGE: 27
- Total: 51

## Top Reasons

- No significant markers found: 27
- Security/vulnerability signal: 17
- Dependency/ecosystem shift: 6
- Direct actionability detected: 4
- Structural shift (engineering refactor/rewrite): 2

## Sources

- GitHub_vscode: 14
- GitHub_unsloth: 13
- GitHub_llama.cpp: 10
- GitHub_langchain: 9
- GitHub_ComfyUI: 5

## Recent Decisions

- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit c2ba3e4 by Sigbjørn Skjæret: add sycl to check-release (#24583)
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit a1d95f3 by John Pollock: Fix nondeterministic video decode at unaligned widths (CORE-299) (#14438)
- PROMOTE score=5 source=GitHub_llama.cpp reason=Security/vulnerability signal preview=Commit 53bd47e by Aldehir Rojas: ui : fix llama-ui-embed crash when no asset dir is given (#24597)
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit 740d347 by comfyanonymous: Remove the comfy python path append.
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit 64cc078 by comfyanonymous: Revert last commit. Last time I use this stupid GitHub app.
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 1e5affb by Tyler James Leonhardt: Fix Claude agent host client tools hanging after confirmation (#321281)  * Fix 
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 678aeb1 by Alexandru Dima: Add agent instructions for opaque editor background and decorations (#321271)  Documen
- PROMOTE score=5 source=GitHub_llama.cpp reason=Security/vulnerability signal preview=Commit 4988f6e by Michael Wand: Add arch support for cohere2-MoE (#24260)  * Add arch support for cohere2-MoE  * Removed
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit f05cf46 by Sigbjørn Skjæret: jinja : fix negative step slice with start/stop values (#24580)
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit 341babc by Sigbjørn Skjæret: jinja : fix split and replace with empty first arg (#24574)  * fix split and replace
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit e8067a8 by Xuan-Son Nguyen: ui: build-time gzip compression (#24571)  * ui: keep original file name and path  * f
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit b664349 by Robin Huang: Expose deploy_environment in /system_stats (#14402)

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
