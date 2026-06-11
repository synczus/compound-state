# Noise Gate Context

_Generated: 2026-06-11 08:24:20 UTC_

## Last 24h

- PROMOTE: 86
- PURGE: 70
- Total: 156

## Top Reasons

- Security/vulnerability signal: 74
- No significant markers found: 70
- Dependency/ecosystem shift: 18
- Direct actionability detected: 14
- Structural shift (engineering refactor/rewrite): 9
- Convergence detected: 8
- Asymmetry/Contrarian signal detected: 2

## Sources

- GitHub_unsloth: 51
- GitHub_vscode: 50
- GitHub_langchain: 36
- GitHub_ComfyUI: 9
- GitHub_llama.cpp: 7
- GitHub_openai-python: 2
- GitHub_AutoGPT: 1

## Recent Decisions

- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit b97e60f by Jukka Seppänen: Fix SCAIL-2 reference mask background convention (#14415)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 1a8ef07 by Bhavya U: Update tool calling prompts and tests (#320906)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit aefd110 by Bhavya U: Cache explorer: conversation-level hit rate, exclude utility models, agent-type filter (#320
- PURGE score=0 source=GitHub_langchain reason=No significant markers found preview=Commit 76c32db by Mason Daugherty: chore(infra): remove noisy annotation (#38063)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 325a129 by Bhavya U: Update messages API and tests (#320910)
- PROMOTE score=4 source=GitHub_llama.cpp reason=Structural shift (engineering refactor/rewrite) preview=Commit 68f3066 by o7si: vocab : refactor normalizer flags into options struct, add strip_accents (#24371)  * vocab : ref
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit 1bfbdb1 by o7si: vocab : adopt leading TemplateProcessing special token as BOS (#24428)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 07e76ab by Martin Aeschlimann: Improve cancellation handling in CachedPromise (#320908)  * Correctly handle cance
- PROMOTE score=3 source=GitHub_langchain reason=Dependency/ecosystem shift preview=Commit f5ef8cb by Mason Daugherty: ci(infra): make release checks handle coordinated package bumps (#38062)  Release val
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 65ec7cb by Martin Aeschlimann: Copilot AH: Simplify and improve customization change handing (#320901)
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit db94854 by Aldehir Rojas: server : skip checkpoints beyond pos_next (#24411)  * server : skip checkpoints beyond 
- PROMOTE score=8 source=GitHub_unsloth reason=Direct actionability detected; Dependency/ecosystem shift preview=Commit 27d43a3 by Daniel Han: MLX CI: drop removed --simple-policy and stale ggml-org pin from the prebuilt step (#6189)

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
