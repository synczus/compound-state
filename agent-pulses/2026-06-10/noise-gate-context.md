# Noise Gate Context

_Generated: 2026-06-10 20:30:19 UTC_

## Last 24h

- PROMOTE: 91
- PURGE: 54
- Total: 145

## Top Reasons

- Security/vulnerability signal: 78
- No significant markers found: 54
- Dependency/ecosystem shift: 14
- Direct actionability detected: 13
- Convergence detected: 10
- Structural shift (engineering refactor/rewrite): 9

## Sources

- GitHub_vscode: 54
- GitHub_unsloth: 50
- GitHub_langchain: 25
- GitHub_ComfyUI: 9
- GitHub_llama.cpp: 5
- GitHub_openai-python: 2

## Recent Decisions

- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit c461d2f by Martin Aeschlimann: CopilotAH: Sort discovered directories/files for faster comparison (#320795)  * Co
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit f7ac402 by Logan Ramos: Support dynamic auto tooltip (#320800)
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 233624a by Arunachalam Nachiappan: Fix image carousel showing UUID on hover in modal editor title (#320739)  fix:
- PROMOTE score=5 source=GitHub_langchain reason=Security/vulnerability signal preview=Commit a063ec2 by Christophe Bornet: chore(core): fix some `any` generics (#34545)  Co-authored-by: Mason Daugherty <git
- PURGE score=0 source=GitHub_langchain reason=No significant markers found preview=Commit 720dfd3 by Christophe Bornet: chore(core): improve typing of Runnable `__or__` (#34530)  `Runnable.__or__`, `Runn
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 3b72a79 by Dmitriy Vasyura: Merge branch 'main' into fix/mcp-redirect-scheme-and-credential-leak
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 29b16ad by Connor Peet: Merge pull request #320347 from g0w6y/fix/mcp-redirect-scheme-and-credential-leak  Valida
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 677bdd2 by Matt Bierner: Merge pull request #320754 from arun-357/fix/image-carousel-caption-markdown  Fix raw ma
- PROMOTE score=4 source=GitHub_langchain reason=Structural shift (engineering refactor/rewrite) preview=Commit 3eee400 by Christophe Bornet: refactor(langchain): refactor `test_create_agent_tool_validation` (#34443)  Simplif
- PROMOTE score=3 source=GitHub_unsloth reason=Dependency/ecosystem shift preview=Commit ec46a55 by Daniel Han: Bump install.sh / install.ps1 pin to unsloth>=2026.6.2 (#6165)
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit d8231ca by Eyera: fix(studio): round compact tooltip corners to 9px (#6163)
- PURGE score=0 source=GitHub_unsloth reason=No significant markers found preview=Commit 52aa248 by Daniel Han: Update CODEOWNERS

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
