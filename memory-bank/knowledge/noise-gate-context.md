# Noise Gate Context

_Generated: 2026-06-13 09:40:02 UTC_

## Last 24h

- PROMOTE: 79
- PURGE: 92
- Total: 171

## Top Reasons

- No significant markers found: 92
- Security/vulnerability signal: 54
- Dependency/ecosystem shift: 26
- Direct actionability detected: 12
- Structural shift (engineering refactor/rewrite): 10
- Convergence detected: 8
- Asymmetry/Contrarian signal detected: 2

## Sources

- GitHub_vscode: 66
- GitHub_unsloth: 63
- GitHub_langchain: 22
- GitHub_llama.cpp: 16
- GitHub_ComfyUI: 4

## Recent Decisions

- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit 8e57c5e by alkinun: Fix Responses tool output content arrays (#6287)  * Fix Responses tool output content arrays 
- PROMOTE score=10 source=GitHub_vscode reason=Direct actionability detected; Security/vulnerability signal preview=Commit bf2334e by Alexandru Dima: ci: add Node.js diagnostic reports for test crash investigation (#321216)  * ci: add N
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 3ef7eb4 by Megan Rogge: Fix question carousel stealing focus from other VS Code UI (#321152)
- PROMOTE score=10 source=GitHub_vscode reason=Direct actionability detected; Security/vulnerability signal preview=Commit 1955c9d by Alexandru Dima: fix: show command and exit code in exec.ps1 error message (#321226)  The default error
- PROMOTE score=8 source=GitHub_unsloth reason=Security/vulnerability signal; Dependency/ecosystem shift preview=Commit a8af0a1 by Daniel Han: Fix llama.cpp prebuilt: skip already-installed same-release fallback (#6285)  * Fix llama.
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit 985792a by Daniel Han: Installer: drop redundant -WindowStyle Hidden from the Windows launcher VBS (#6284)  * Ins
- PURGE score=0 source=GitHub_langchain reason=No significant markers found preview=Commit 11429a9 by Mason Daugherty: fix(openai): avoid sync token reads in Codex streaming (#38128)  Codex streaming now 
- PROMOTE score=5 source=GitHub_langchain reason=Security/vulnerability signal preview=Commit 37b339f by Mason Daugherty: fix(openai): build Codex async headers off the event loop in `_agenerate` (#38129)  T
- PURGE score=0 source=GitHub_langchain reason=No significant markers found preview=Commit 879cad0 by Mason Daugherty: release(openai): 1.3.2 (#38130)
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit d8a24cc by Georgi Gerganov: fit : wrap llama_device_memory_data (#24522)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit cd6495a by Vijay Upadya: Enable gemini-3.5-flash prompt update exp (#321231)  gemini prompt update
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit 502d4ad by Michael Han: Tidy update banner and auth button spacing (#6279)  * Fix update banner button spacing  *

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
