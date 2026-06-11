# Noise Gate Context

_Generated: 2026-06-11 06:11:59 UTC_

## Last 24h

- PROMOTE: 86
- PURGE: 58
- Total: 144

## Top Reasons

- Security/vulnerability signal: 75
- No significant markers found: 58
- Dependency/ecosystem shift: 17
- Direct actionability detected: 13
- Convergence detected: 9
- Structural shift (engineering refactor/rewrite): 8
- Asymmetry/Contrarian signal detected: 2

## Sources

- GitHub_unsloth: 51
- GitHub_vscode: 45
- GitHub_langchain: 31
- GitHub_ComfyUI: 8
- GitHub_llama.cpp: 6
- GitHub_openai-python: 2
- GitHub_AutoGPT: 1

## Recent Decisions

- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit 53af337 by oobabooga: Studio: forward `preserve_thinking` + `reasoning_effort` on the OpenAI passthrough (#6171) 
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit 91187c5 by Barish Ozbay: Improve context window resizing for SCAIL2 (CORE-286) (#14394)
- PURGE score=0 source=GitHub_unsloth reason=No significant markers found preview=Commit 8961cf1 by Michael Han: Give dark mode toasts a shadow and background separation (#6186)
- PURGE score=0 source=GitHub_langchain reason=No significant markers found preview=Commit d5f7d33 by Christophe Bornet: chore(langchain): add overloads to `create_agent` (#34309)  This way mypy can infer
- PURGE score=0 source=GitHub_unsloth reason=No significant markers found preview=Commit 9e2d17c by Daniel Han: Tests: follow Compare chat into the More submenu in the extra UI driver (#6177)  PR #6153 
- PROMOTE score=5 source=GitHub_langchain reason=Security/vulnerability signal preview=Commit 86428c6 by Mason Daugherty: fix(core,openai): normalize v1 streamed tool calls (#35983)  OpenAI Chat Completions 
- PROMOTE score=13 source=GitHub_langchain reason=Direct actionability detected; Security/vulnerability signal; Dependency/ecosystem shift preview=Commit 1de100f by Christophe Bornet: chore(infra): bump mypy to 2.1 and unify type-check config across the monorepo (#36
- PROMOTE score=12 source=GitHub_unsloth reason=Asymmetry/Contrarian signal detected; Security/vulnerability signal; Convergence detected preview=Commit bf2cd74 by Leo Borcherding: Fix installer selecting ROCm torch on NVIDIA Linux hosts (#6174)  * fix: prevent ROCm
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit d7ce0ce by Don Jayamanne: Enhance agent and skill discovery: include descriptions in session customization tests 
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit 74ee826 by Comfy Org PR Bot: chore(openapi): sync shared API contract from cloud@e3c52ad (#14406)
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit 33e6ebd by comfyanonymous: I don't think this actually works anymore. (#14403)
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit bda19b2 by rattus: ops: tolerate already force casted dynamic weight (#14410)  Some custom nodes .to weights comp

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
