# Noise Gate Context

_Generated: 2026-06-09 12:12:40 UTC_

## Last 24h

- PROMOTE: 47
- PURGE: 55
- Total: 102

## Top Reasons

- No significant markers found: 55
- Security/vulnerability signal: 36
- Dependency/ecosystem shift: 7
- Convergence detected: 7
- Structural shift (engineering refactor/rewrite): 5
- Direct actionability detected: 5

## Sources

- GitHub_vscode: 23
- GitHub_llama.cpp: 22
- GitHub_unsloth: 15
- GitHub_ollama: 11
- GitHub_ComfyUI: 11
- GitHub_langchain: 10
- GitHub_openai-python: 10

## Recent Decisions

- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit 33f4397 by Wasim Yousef Said: Studio fix recipe dataset preview (#6031)  * Studio: fix recipe dataset preview  * 
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit a66cbe3 by Lee Murray: Update @vscode/codicons to version 0.0.46-16 and add 'runCompact' icon registration (#3204
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit d6d0ce8 by Jeff Bolz: vulkan: reduce iq1 shared memory usage for mul_mm (#24287)
- PURGE score=0 source=GitHub_unsloth reason=No significant markers found preview=Commit aec41d1 by Eyera: feat(studio): Hub + Download Manager (#5916)  Adds the Studio Hub and download manager: browse 
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit b4e3dc6 by Ruben Ortlam: vulkan: add `v_dot2_f32_f16` support in matrix-matrix multiplication and Flash Attention
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 0c61709 by Benjamin Christopher Simmonds: sessions: experiment to move harness picker below input (#320584)  Add 
- PROMOTE score=5 source=GitHub_llama.cpp reason=Security/vulnerability signal preview=Commit ae735b1 by Nick Towle: ui: Fix excessive style recalculation on hover (#24243)
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit 1e91256 by jacekpoplawski: server: log prompts to directory (#22031)  * server: log prompts to directory  Add `--
- PROMOTE score=4 source=GitHub_llama.cpp reason=Structural shift (engineering refactor/rewrite) preview=Commit 9682e35 by Xuan-Son Nguyen: mtmd: refactor video subproc handling (#24316)  * mtmd: refactor video subproc handli
- PROMOTE score=5 source=GitHub_llama.cpp reason=Security/vulnerability signal preview=Commit efbacf8 by Pascal: ui: fix mobile chat form overflow and bust stale bundle cache (#24158)
- PROMOTE score=8 source=GitHub_llama.cpp reason=Security/vulnerability signal; Dependency/ecosystem shift preview=Commit 2602169 by Pascal: ggml : add GGML_OP_COL2IM_1D (#24206)  * cpu: add GGML_OP_COL2IM_1D  Add the overlap-add (scat
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 14689db by Christof Marti: Improve smoke test reliability in CI (#317981)

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
