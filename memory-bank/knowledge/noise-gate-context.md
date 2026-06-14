# Noise Gate Context

_Generated: 2026-06-14 09:57:39 UTC_

## Last 24h

- PROMOTE: 16
- PURGE: 21
- Total: 37

## Top Reasons

- No significant markers found: 21
- Security/vulnerability signal: 10
- Dependency/ecosystem shift: 5
- Direct actionability detected: 2
- Structural shift (engineering refactor/rewrite): 1

## Sources

- GitHub_llama.cpp: 12
- GitHub_vscode: 10
- GitHub_unsloth: 10
- GitHub_ComfyUI: 5

## Recent Decisions

- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit 6e14286 by Michael Wand: cli : fix not copying preserved tokens (#24258)
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit 8ed274e by Bartowski: Add cohere2moe to llama-vocab for TINY_AYA (#24601)
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 4ac5322 by Daniel Imms: fix(terminal): track ligatures addon config for change detection (#318992)  Store ILigatu
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit 4672211 by Sigbjørn Skjæret: ci : use CUDA label for cuda backend (#24594)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 9b43a71 by RedCMD: fix: Restrict continue comment to whitespace separated slashes (#321230)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit c25b323 by Kyle Cutler: Browser: fix URLs incorrectly matching file:// scheme (#321302)
- PURGE score=0 source=GitHub_unsloth reason=No significant markers found preview=Commit a3ca5d2 by oobabooga: Studio: don't silently fall back to a CPU prebuilt on NVIDIA Linux GPU hosts (#6310)
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit c2ba3e4 by Sigbjørn Skjæret: add sycl to check-release (#24583)
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit a1d95f3 by John Pollock: Fix nondeterministic video decode at unaligned widths (CORE-299) (#14438)
- PROMOTE score=5 source=GitHub_llama.cpp reason=Security/vulnerability signal preview=Commit 53bd47e by Aldehir Rojas: ui : fix llama-ui-embed crash when no asset dir is given (#24597)
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit 740d347 by comfyanonymous: Remove the comfy python path append.
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit 64cc078 by comfyanonymous: Revert last commit. Last time I use this stupid GitHub app.

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
