# Noise Gate Context

_Generated: 2026-06-10 07:06:38 UTC_

## Last 24h

- PROMOTE: 58
- PURGE: 69
- Total: 127

## Top Reasons

- No significant markers found: 69
- Security/vulnerability signal: 46
- Structural shift (engineering refactor/rewrite): 8
- Direct actionability detected: 6
- Dependency/ecosystem shift: 6
- Convergence detected: 6

## Sources

- GitHub_vscode: 59
- GitHub_langchain: 20
- GitHub_llama.cpp: 15
- GitHub_ComfyUI: 15
- GitHub_unsloth: 11
- GitHub_ollama: 6
- GitHub_AutoGPT: 1

## Recent Decisions

- PROMOTE score=8 source=GitHub_unsloth reason=Security/vulnerability signal; Convergence detected preview=Commit fcfbf16 by Daniel Han: studio(ui): use the --primary brand token for the avatar fallback color (#5987)  * studio(
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit 03349d1 by Matt Van Horn: feat: support text-only loading of Gemma 3 27B via FastLanguageModel (skip SiglipVision
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 77fc8de by Justin Chen: agent host pickers: align picker text + update styling (#320687)  * align picker text + u
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit cb86056 by Connor Peet: agentHost: describe empty attachment tool results (#320707)  When a successful client too
- PROMOTE score=5 source=GitHub_ComfyUI reason=Security/vulnerability signal preview=Commit 039ed38 by Matt Miller: fix(assets): remove unused delete_content param from deleteAsset (#14241)  * fix(assets):
- PURGE score=0 source=GitHub_unsloth reason=No significant markers found preview=Commit 8848a31 by Daniel Han: Studio: clean-room compact RAG (knowledge bases, hybrid search, fast indexing) (#5910)  Ad
- PURGE score=0 source=GitHub_langchain reason=No significant markers found preview=Commit 64ee4d8 by Mason Daugherty: release(groq): 1.1.3 (#38009)  Closes #37996
- PROMOTE score=3 source=GitHub_langchain reason=Convergence detected preview=Commit bee470c by Mason Daugherty: ci(infra): attach release artifacts from package dist directory (#38010)  The release
- PROMOTE score=15 source=GitHub_ComfyUI reason=Structural shift (engineering refactor/rewrite); Security/vulnerability signal; Dependency/ecosystem shift; Convergence  preview=Commit 84e0692 by Matt Miller: feat(assets): cursor-based pagination on GET /api/assets (#14014)  * spec(assets): add cu
- PROMOTE score=8 source=GitHub_vscode reason=Security/vulnerability signal; Dependency/ecosystem shift preview=Commit 73d65f0 by dileepyavan: Cherry pick/msrc 1.123 to release 1.123 (#55) (#320699)  * OTel visibility in Copilot Cha
- PURGE score=0 source=GitHub_langchain reason=No significant markers found preview=Commit b9fb3da by Mason Daugherty: ci(model-profiles): skip profile refresh workflow on forks (#38008)  Closes #37997  F
- PROMOTE score=7 source=GitHub_ComfyUI reason=Structural shift (engineering refactor/rewrite); Convergence detected preview=Commit a76bb43 by Matt Miller: chore(assets): drop vestigial tags.tag_type column (#14248)  tag_type was always "user" i

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
