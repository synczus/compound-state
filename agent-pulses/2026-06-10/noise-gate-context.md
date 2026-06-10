# Noise Gate Context

_Generated: 2026-06-10 04:11:20 UTC_

## Last 24h

- PROMOTE: 58
- PURGE: 68
- Total: 126

## Top Reasons

- No significant markers found: 68
- Security/vulnerability signal: 43
- Direct actionability detected: 7
- Structural shift (engineering refactor/rewrite): 7
- Convergence detected: 6
- Dependency/ecosystem shift: 5

## Sources

- GitHub_vscode: 59
- GitHub_langchain: 18
- GitHub_llama.cpp: 17
- GitHub_ComfyUI: 14
- GitHub_unsloth: 11
- GitHub_ollama: 6
- GitHub_AutoGPT: 1

## Recent Decisions

- PROMOTE score=8 source=GitHub_vscode reason=Security/vulnerability signal; Dependency/ecosystem shift preview=Commit 73d65f0 by dileepyavan: Cherry pick/msrc 1.123 to release 1.123 (#55) (#320699)  * OTel visibility in Copilot Cha
- PURGE score=0 source=GitHub_langchain reason=No significant markers found preview=Commit b9fb3da by Mason Daugherty: ci(model-profiles): skip profile refresh workflow on forks (#38008)  Closes #37997  F
- PROMOTE score=7 source=GitHub_ComfyUI reason=Structural shift (engineering refactor/rewrite); Convergence detected preview=Commit a76bb43 by Matt Miller: chore(assets): drop vestigial tags.tag_type column (#14248)  tag_type was always "user" i
- PROMOTE score=5 source=GitHub_ComfyUI reason=Security/vulnerability signal preview=Commit f350acd by Kohaku-Blueleaf: [Trainer/bug] Ensure model is not inference mode (CORE-72) (#13400)  * Ensure model i
- PURGE score=0 source=GitHub_langchain reason=No significant markers found preview=Commit 6fde3f0 by Mason Daugherty: docs(infra): clarify PR description expectations (#38007)  PR authors get clearer gui
- PROMOTE score=5 source=GitHub_langchain reason=Security/vulnerability signal preview=Commit 8bc9630 by Mason Daugherty: fix(core): accept sequence tool error content (#38005)  `handle_tool_error` callables
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 1b342df by Rob Lourens: Fix double-escaped entities in renderAsPlaintext code spans (#320336)  The plaintext mark
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit 46d45aa by Comfy Org PR Bot: chore(openapi): sync shared API contract from cloud@ca12913 (#14367)
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit 5ece24e by Talmaj: Depth anything 3 (Core-135) (#13853)  Co-authored-by: Alexis Rolland <alexisrolland@hotmail.co
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit 5fcf7a4 by comfyanonymous: Always enable cuda malloc on cu130 and higher. (#14381)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 271a21a by Rob Lourens: chat: use Copilot icon for Agent Host sessions in editor window (#320700)  * chat: use Co
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 3363bdb by Rob Lourens: chat: Include Copilot logs in Agent Host debug export (#320677)  * chat: include Copilot 

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
