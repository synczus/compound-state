# Noise Gate Context

_Generated: 2026-06-11 15:53:15 UTC_

## Last 24h

- PROMOTE: 93
- PURGE: 79
- Total: 172

## Top Reasons

- No significant markers found: 79
- Security/vulnerability signal: 76
- Dependency/ecosystem shift: 21
- Convergence detected: 15
- Direct actionability detected: 14
- Structural shift (engineering refactor/rewrite): 11
- Asymmetry/Contrarian signal detected: 2

## Sources

- GitHub_unsloth: 57
- GitHub_vscode: 57
- GitHub_langchain: 35
- GitHub_ComfyUI: 11
- GitHub_llama.cpp: 8
- GitHub_openai-python: 2
- GitHub_AutoGPT: 2

## Recent Decisions

- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit 73eed19 by Tai An: fix(_utils): coerce _is_package_available tuple to bool for flash_attn/vllm checks (#6168)  tr
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 2d1484f by Logan Ramos: Improve markdown paste of nested html tags (#320967)  * Improve markdown paste of nested 
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit 181288e by Ritwij Aryan Parmar: fix(studio): handle empty Responses tool output (#6167)  • fix: handle empty resp
- PURGE score=0 source=GitHub_unsloth reason=No significant markers found preview=Commit 3964f44 by Leo Borcherding: fix(rocm): stop overwriting ROCR_VISIBLE_DEVICES in apply_gpu_ids (#6123)  * fix(rocm
- PROMOTE score=8 source=GitHub_unsloth reason=Security/vulnerability signal; Convergence detected preview=Commit 120daf9 by Viktor Ferenczi: fix(studio/rocm): don't stack ROCR_VISIBLE_DEVICES on HIP_VISIBLE_DEVICES (#6176)  Wh
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit 004577c by Nilay: studio: show MCP "Import config" on the add-server form (#6030)  * studio: import MCP servers f
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit f64c3c8 by Nilay: Studio: add `unsloth chat` CLI command (#6170)  * Studio: add `unsloth chat` CLI command  Inter
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 916a11c by Lee Murray: Merge pull request #320934 from microsoft/mrleemurray/design-dot-md  Add design tokens doc
- PROMOTE score=8 source=GitHub_unsloth reason=Security/vulnerability signal; Convergence detected preview=Commit bc85ecd by Daniel Han: Studio: report the real llama-server context window and add an opt-in overflow policy for 
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit 3733e0b by Daniel Han: fix(studio): surface live step with null loss through the SSE progress stream (#6206)  * f
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 450a770 by Christof Marti: Try fix flaky test (#320956)
- PROMOTE score=8 source=GitHub_unsloth reason=Security/vulnerability signal; Dependency/ecosystem shift preview=Commit 7467064 by Burak Emir: Bump hono to 4.12.21, fixes CVE-2026-47676 (#6014)

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
