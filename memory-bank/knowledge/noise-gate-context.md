# Noise Gate Context

_Generated: 2026-06-09 08:01:17 UTC_

## Last 24h

- PROMOTE: 42
- PURGE: 48
- Total: 90

## Top Reasons

- No significant markers found: 48
- Security/vulnerability signal: 32
- Convergence detected: 7
- Dependency/ecosystem shift: 6
- Direct actionability detected: 5
- Structural shift (engineering refactor/rewrite): 4

## Sources

- GitHub_vscode: 20
- GitHub_llama.cpp: 15
- GitHub_unsloth: 13
- GitHub_ollama: 11
- GitHub_ComfyUI: 11
- GitHub_langchain: 10
- GitHub_openai-python: 10

## Recent Decisions

- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 58c0981 by Henning Dieterichs: Registers @vscode/markdown-editor in markdown-language-features extension
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit ffd6d6e by Henning Dieterichs: Fixes CI
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit 961e9a3 by fiesh: server : do not clear slots without unified KV cache (#24190)  * Always export idle slots to RA
- PURGE score=0 source=GitHub_ollama reason=No significant markers found preview=Commit 4c97a94 by Jesse Gross: mlxthread: preserve the original stack when worker work panics  Work that panics on the l
- PURGE score=0 source=GitHub_ollama reason=No significant markers found preview=Commit 07588c6 by Jesse Gross: mlxrunner/cache: split KVCache and RotatingKVCache into their own files  cache.go had gro
- PROMOTE score=5 source=GitHub_ollama reason=Direct actionability detected preview=Commit 177aefb by Jesse Gross: nn/recurrent: return per-boundary states from the gated-delta kernels  CausalConv1D and G
- PURGE score=0 source=GitHub_ollama reason=No significant markers found preview=Commit d006220 by Jesse Gross: mlxrunner: drive MTP speculation through cache snapshots  Speculation used a parallel hie
- PURGE score=0 source=GitHub_ollama reason=No significant markers found preview=Commit ded2db7 by Jesse Gross: mlxrunner: capture prefill snapshots across the forward  Prefill no longer splits its bat
- PURGE score=0 source=GitHub_ollama reason=No significant markers found preview=Commit 1abd56b by Jesse Gross: mlxrunner: record committed MTP drafts before streaming them  The batched MTP accept path
- PROMOTE score=5 source=GitHub_llama.cpp reason=Security/vulnerability signal preview=Commit fd3271e by Yash Raj Pandey: ggml-cpu : fix rms_norm_back wrong output under in-place aliasing (#24305)  * ggml-cp
- PROMOTE score=5 source=GitHub_llama.cpp reason=Security/vulnerability signal preview=Commit f0152ef by Sigbjørn Skjæret: models : fix plamo2 attention_key/value_length regression (#24317)
- PROMOTE score=3 source=GitHub_unsloth reason=Convergence detected preview=Commit 8292e69 by Daniel Han: Studio: make code comments and docstrings more succinct (#6029)  Trim and tighten code com

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
