# Noise Gate Context

_Generated: 2026-06-10 21:34:48 UTC_

## Last 24h

- PROMOTE: 87
- PURGE: 53
- Total: 140

## Top Reasons

- Security/vulnerability signal: 75
- No significant markers found: 53
- Dependency/ecosystem shift: 15
- Direct actionability detected: 12
- Structural shift (engineering refactor/rewrite): 9
- Convergence detected: 9

## Sources

- GitHub_vscode: 50
- GitHub_unsloth: 49
- GitHub_langchain: 24
- GitHub_ComfyUI: 9
- GitHub_llama.cpp: 5
- GitHub_openai-python: 2
- GitHub_AutoGPT: 1

## Recent Decisions

- PURGE score=0 source=GitHub_langchain reason=No significant markers found preview=Commit 1aa1704 by Mason Daugherty: release(langchain-classic): 1.0.8 (#38033)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit e1db287 by Zhichao Li: Merge pull request #320704 from microsoft/otel-streaming-signals  Emit gen_ai streaming OT
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 41c7c99 by Justin Chen: fix image thumbnail crash on aux windows (#320843)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 88acbda by Justin Chen: fill chat bubble to fit code block (#320839)
- PROMOTE score=10 source=GitHub_vscode reason=Direct actionability detected; Security/vulnerability signal preview=Commit f57a83c by Tyler James Leonhardt: Distribute Claude and Codex agent SDKs via product.json (#320709)  * Add tar to
- PROMOTE score=5 source=GitHub_langchain reason=Security/vulnerability signal preview=Commit f89f4c5 by Mason Daugherty: fix(core): support content block tokens in callbacks (#34739)  Supersedes #34727 Clos
- PURGE score=0 source=GitHub_langchain reason=No significant markers found preview=Commit 2e832c2 by Mason Daugherty: release(core): 1.4.4 (#38031)
- PROMOTE score=8 source=GitHub_langchain reason=Security/vulnerability signal; Dependency/ecosystem shift preview=Commit 8ac91e3 by Mason Daugherty: hotfix(core): bump lockfile(s) (#38032)
- PURGE score=0 source=GitHub_AutoGPT reason=No significant markers found preview=Commit 5b603c0 by Nicholas Tindle: Merge branch 'master' into dev
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit c461d2f by Martin Aeschlimann: CopilotAH: Sort discovered directories/files for faster comparison (#320795)  * Co
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit f7ac402 by Logan Ramos: Support dynamic auto tooltip (#320800)
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 233624a by Arunachalam Nachiappan: Fix image carousel showing UUID on hover in modal editor title (#320739)  fix:

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
