# Noise Gate Context

_Generated: 2026-06-10 19:00:44 UTC_

## Last 24h

- PROMOTE: 89
- PURGE: 56
- Total: 145

## Top Reasons

- Security/vulnerability signal: 76
- No significant markers found: 56
- Dependency/ecosystem shift: 14
- Direct actionability detected: 13
- Structural shift (engineering refactor/rewrite): 10
- Convergence detected: 10

## Sources

- GitHub_vscode: 52
- GitHub_unsloth: 50
- GitHub_langchain: 25
- GitHub_ComfyUI: 10
- GitHub_llama.cpp: 6
- GitHub_openai-python: 2

## Recent Decisions

- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 677bdd2 by Matt Bierner: Merge pull request #320754 from arun-357/fix/image-carousel-caption-markdown  Fix raw ma
- PROMOTE score=4 source=GitHub_langchain reason=Structural shift (engineering refactor/rewrite) preview=Commit 3eee400 by Christophe Bornet: refactor(langchain): refactor `test_create_agent_tool_validation` (#34443)  Simplif
- PROMOTE score=3 source=GitHub_unsloth reason=Dependency/ecosystem shift preview=Commit ec46a55 by Daniel Han: Bump install.sh / install.ps1 pin to unsloth>=2026.6.2 (#6165)
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit d8231ca by Eyera: fix(studio): round compact tooltip corners to 9px (#6163)
- PURGE score=0 source=GitHub_unsloth reason=No significant markers found preview=Commit 52aa248 by Daniel Han: Update CODEOWNERS
- PURGE score=0 source=GitHub_unsloth reason=No significant markers found preview=Commit 3b662d1 by Daniel Han: Update _utils.py
- PURGE score=0 source=GitHub_unsloth reason=No significant markers found preview=Commit 5f11182 by Daniel Han: Update pyproject.toml
- PURGE score=0 source=GitHub_langchain reason=No significant markers found preview=Commit 92ee772 by Alexander Olsen: feat(langchain): add `ProviderToolSearchMiddleware` (#37969)  [Docs](https://github.c
- PROMOTE score=5 source=GitHub_langchain reason=Security/vulnerability signal preview=Commit 7ffe092 by Christophe Bornet: style(langchain): add ruff rules ARG (#34435)  In this order: * used `@override` wh
- PURGE score=0 source=GitHub_langchain reason=No significant markers found preview=Commit 3d3a4c2 by Mason Daugherty: release(langchain): 1.3.7 (#38024)
- PROMOTE score=10 source=GitHub_unsloth reason=Direct actionability detected; Security/vulnerability signal preview=Commit 50e4e9c by Daniel Han: Studio: gracefully disable MTP when the model has no head or drafter (#6159)  * Studio: gr
- PROMOTE score=3 source=GitHub_unsloth reason=Dependency/ecosystem shift preview=Commit aa3b46f by Daniel Han: Studio: show the llama.cpp update banner sooner and keep it until dismissed (#6162)  Follo

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
