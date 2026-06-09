# Noise Gate Context

_Generated: 2026-06-09 04:13:56 UTC_

## Last 24h

- PROMOTE: 37
- PURGE: 66
- Total: 103

## Top Reasons

- No significant markers found: 66
- Security/vulnerability signal: 30
- Dependency/ecosystem shift: 6
- Structural shift (engineering refactor/rewrite): 5
- Direct actionability detected: 4
- Convergence detected: 4

## Sources

- Telegram: 30
- GitHub_vscode: 16
- GitHub_llama.cpp: 11
- GitHub_ComfyUI: 11
- GitHub_langchain: 10
- GitHub_openai-python: 10
- GitHub_unsloth: 10
- GitHub_ollama: 5

## Recent Decisions

- PROMOTE score=5 source=GitHub_ComfyUI reason=Security/vulnerability signal preview=Commit f899992 by Alexis Rolland: fix: Add back apply_rotary_emb for Qwen Image (#14364)
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit 3ac3c20 by Reese Levine: ggml-webgpu: Add clang-format job (#24308)  * Add clang-format job  * try local formatti
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit cb9600e by Connor Peet: Only show WSL remote picker option on Windows (#320543)  Fixes #320541  Co-authored-by: C
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit e8303fa by Connor Peet: Add tooltips to agent host session config pickers (#320542)  * Add tooltips to agent host
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit cb9f639 by Comfy Org PR Bot: chore(openapi): sync shared API contract from cloud@5273c30 (#14266)
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 7facb8e by Rob Lourens: Make Agent Host git-blob URIs label friendly (#317450)  * Make git blob URIs label friend
- PROMOTE score=9 source=GitHub_vscode reason=Structural shift (engineering refactor/rewrite); Security/vulnerability signal preview=Commit cdb2a31 by Don Jayamanne: Disable VS Code completions as  agent-host backed sessions, provide their own completio
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 91e5eeb by vs-code-engineering[bot]: [cherry-pick] Render keybindings for OpenInVSCode and OpenWorkspaceInAgents 
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 2f63868 by Harald Kirschner: Fix Chronicle cloud search timeouts with 7-day default window (#318620)  - Change de
- PROMOTE score=8 source=GitHub_unsloth reason=Security/vulnerability signal; Convergence detected preview=Commit cf97fae by Michael Han: Studio: keep chat in place when composer attachments resize it (#6070)  * Studio: keep ch
- PROMOTE score=4 source=GitHub_unsloth reason=Structural shift (engineering refactor/rewrite) preview=Commit b2b4e4c by Daniel Han: CI: allowlist deepseek_ocr2 in the compiler full-model-sweep (#6085)  transformers-latest 
- PROMOTE score=12 source=GitHub_unsloth reason=Structural shift (engineering refactor/rewrite); Security/vulnerability signal; Convergence detected preview=Commit e20a6c3 by Daniel Han: Restore KTO logps truncation guard for TRL (re-apply dropped #5996) (#6086)  * Restore KTO

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
