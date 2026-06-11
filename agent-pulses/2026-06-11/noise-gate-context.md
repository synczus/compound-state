# Noise Gate Context

_Generated: 2026-06-11 04:16:12 UTC_

## Last 24h

- PROMOTE: 87
- PURGE: 58
- Total: 145

## Top Reasons

- Security/vulnerability signal: 75
- No significant markers found: 58
- Dependency/ecosystem shift: 17
- Direct actionability detected: 12
- Convergence detected: 11
- Structural shift (engineering refactor/rewrite): 9
- Asymmetry/Contrarian signal detected: 2

## Sources

- GitHub_unsloth: 50
- GitHub_vscode: 47
- GitHub_langchain: 30
- GitHub_ComfyUI: 9
- GitHub_llama.cpp: 6
- GitHub_openai-python: 2
- GitHub_AutoGPT: 1

## Recent Decisions

- PROMOTE score=12 source=GitHub_unsloth reason=Asymmetry/Contrarian signal detected; Security/vulnerability signal; Convergence detected preview=Commit bf2cd74 by Leo Borcherding: Fix installer selecting ROCm torch on NVIDIA Linux hosts (#6174)  * fix: prevent ROCm
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit d7ce0ce by Don Jayamanne: Enhance agent and skill discovery: include descriptions in session customization tests 
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit 74ee826 by Comfy Org PR Bot: chore(openapi): sync shared API contract from cloud@e3c52ad (#14406)
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit 33e6ebd by comfyanonymous: I don't think this actually works anymore. (#14403)
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit bda19b2 by rattus: ops: tolerate already force casted dynamic weight (#14410)  Some custom nodes .to weights comp
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 1677f39 by Justin Chen: toolbar ux fix for context and collapse (#320870)
- PROMOTE score=4 source=GitHub_vscode reason=Structural shift (engineering refactor/rewrite) preview=Commit 05c3dde by Don Jayamanne: refactor: replace IChatWidgetService with ISessionsManagementService in SlashCommandHan
- PURGE score=0 source=GitHub_langchain reason=No significant markers found preview=Commit 030ec60 by Mason Daugherty: release(core): 1.4.5 (#38056)
- PURGE score=0 source=GitHub_langchain reason=No significant markers found preview=Commit 904abb1 by Mason Daugherty: release(model-profiles): 0.0.6 (#38057)
- PROMOTE score=13 source=GitHub_langchain reason=Direct actionability detected; Security/vulnerability signal; Convergence detected preview=Commit 4388036 by Mason Daugherty: feat(standard-tests): validate tool call chunks during streaming (#34707)  As a LangC
- PURGE score=0 source=GitHub_langchain reason=No significant markers found preview=Commit ffaeba8 by Mason Daugherty: ci(infra): validate release versions before publishing (#38055)  Release jobs can now
- PROMOTE score=5 source=GitHub_langchain reason=Security/vulnerability signal preview=Commit 7cc9d0c by Mason Daugherty: fix(core): async tracer `on_chat_model_start` fallback in sync context (#35233)  Fixe

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
