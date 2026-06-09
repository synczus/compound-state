# Noise Gate Context

_Generated: 2026-06-09 11:07:54 UTC_

## Last 24h

- PROMOTE: 46
- PURGE: 51
- Total: 97

## Top Reasons

- No significant markers found: 51
- Security/vulnerability signal: 35
- Dependency/ecosystem shift: 7
- Convergence detected: 7
- Structural shift (engineering refactor/rewrite): 5
- Direct actionability detected: 5

## Sources

- GitHub_vscode: 22
- GitHub_llama.cpp: 20
- GitHub_unsloth: 13
- GitHub_ollama: 11
- GitHub_ComfyUI: 11
- GitHub_langchain: 10
- GitHub_openai-python: 10

## Recent Decisions

- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 0c61709 by Benjamin Christopher Simmonds: sessions: experiment to move harness picker below input (#320584)  Add 
- PROMOTE score=5 source=GitHub_llama.cpp reason=Security/vulnerability signal preview=Commit ae735b1 by Nick Towle: ui: Fix excessive style recalculation on hover (#24243)
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit 1e91256 by jacekpoplawski: server: log prompts to directory (#22031)  * server: log prompts to directory  Add `--
- PROMOTE score=4 source=GitHub_llama.cpp reason=Structural shift (engineering refactor/rewrite) preview=Commit 9682e35 by Xuan-Son Nguyen: mtmd: refactor video subproc handling (#24316)  * mtmd: refactor video subproc handli
- PROMOTE score=5 source=GitHub_llama.cpp reason=Security/vulnerability signal preview=Commit efbacf8 by Pascal: ui: fix mobile chat form overflow and bust stale bundle cache (#24158)
- PROMOTE score=8 source=GitHub_llama.cpp reason=Security/vulnerability signal; Dependency/ecosystem shift preview=Commit 2602169 by Pascal: ggml : add GGML_OP_COL2IM_1D (#24206)  * cpu: add GGML_OP_COL2IM_1D  Add the overlap-add (scat
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 14689db by Christof Marti: Improve smoke test reliability in CI (#317981)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 58c0981 by Henning Dieterichs: Registers @vscode/markdown-editor in markdown-language-features extension
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit ffd6d6e by Henning Dieterichs: Fixes CI
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit 961e9a3 by fiesh: server : do not clear slots without unified KV cache (#24190)  * Always export idle slots to RA
- PURGE score=0 source=GitHub_ollama reason=No significant markers found preview=Commit 4c97a94 by Jesse Gross: mlxthread: preserve the original stack when worker work panics  Work that panics on the l
- PURGE score=0 source=GitHub_ollama reason=No significant markers found preview=Commit 07588c6 by Jesse Gross: mlxrunner/cache: split KVCache and RotatingKVCache into their own files  cache.go had gro

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
