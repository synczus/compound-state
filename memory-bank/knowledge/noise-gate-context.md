# Noise Gate Context

_Generated: 2026-06-11 12:21:12 UTC_

## Last 24h

- PROMOTE: 88
- PURGE: 69
- Total: 157

## Top Reasons

- Security/vulnerability signal: 73
- No significant markers found: 69
- Dependency/ecosystem shift: 19
- Direct actionability detected: 12
- Structural shift (engineering refactor/rewrite): 9
- Convergence detected: 9
- Asymmetry/Contrarian signal detected: 2

## Sources

- GitHub_vscode: 52
- GitHub_unsloth: 47
- GitHub_langchain: 36
- GitHub_ComfyUI: 10
- GitHub_llama.cpp: 8
- GitHub_openai-python: 2
- GitHub_AutoGPT: 2

## Recent Decisions

- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit 4902446 by Lee Jackson: Studio: ignore unsupported env proxy during Studio startup (#6102)  * fix: ignore unsuppo
- PROMOTE score=8 source=GitHub_unsloth reason=Security/vulnerability signal; Convergence detected preview=Commit d0ffe26 by Daniel Han: Keep audio feature extractors right padded when loading processors (#6157)  * Keep audio f
- PROMOTE score=13 source=GitHub_unsloth reason=Direct actionability detected; Security/vulnerability signal; Dependency/ecosystem shift preview=Commit 2db9fad by Daniel Han: Installer: GPU detection follow-ups after #6174 (poisoned venv repair, llama.cpp routing, 
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 44f9066 by Lee Murray: Merge pull request #319736 from microsoft/mrleemurray/conventional-turquoise-termite  Impr
- PROMOTE score=7 source=GitHub_unsloth reason=Structural shift (engineering refactor/rewrite); Convergence detected preview=Commit 28fe978 by Daniel Han: Lint CI: diff import-hoist check against the PR merge-base, not the base tip (#6190)  The 
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit fbaf527 by Daniel Han: Add FastDiffusionModel slow path for text-diffusion models (DiffusionGemma) (#6158)  * Add
- PROMOTE score=3 source=GitHub_vscode reason=Dependency/ecosystem shift preview=Commit 847d569 by Don Jayamanne: chore: update @github/copilot and related dependencies to version 1.0.61 (#320868)  * c
- PROMOTE score=8 source=GitHub_AutoGPT reason=Security/vulnerability signal; Dependency/ecosystem shift preview=Commit ba178a7 by Ubbe: fix(frontend): harden paywall flows for half-dead sessions (#13333)  ### Why / What / How  **Why
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 39d8817 by Martin Aeschlimann: IChatRequestModeInfo: clarify property names (#319903)  * IChatRequestModeInfo: cl
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit a7680b0 by Martin Aeschlimann: Fix CachedPromise to reset state on cancellation of in-flight computations (#32092
- PROMOTE score=8 source=GitHub_unsloth reason=Security/vulnerability signal; Dependency/ecosystem shift preview=Commit 898d3dd by Daniel Han: Studio: offer the in-app llama.cpp update for source-build (markerless) installs (#6188)  
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit ec1935c by Don Jayamanne: Revert "add env var to AH to tag our CAPI traffic (#320814)" (#320923)  This reverts co

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
