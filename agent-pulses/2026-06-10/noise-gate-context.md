# Noise Gate Context

_Generated: 2026-06-10 16:15:05 UTC_

## Last 24h

- PROMOTE: 85
- PURGE: 52
- Total: 137

## Top Reasons

- Security/vulnerability signal: 74
- No significant markers found: 52
- Dependency/ecosystem shift: 14
- Direct actionability detected: 13
- Convergence detected: 9
- Structural shift (engineering refactor/rewrite): 8

## Sources

- GitHub_vscode: 57
- GitHub_unsloth: 41
- GitHub_langchain: 20
- GitHub_ComfyUI: 10
- GitHub_llama.cpp: 7
- GitHub_openai-python: 2

## Recent Decisions

- PROMOTE score=13 source=GitHub_unsloth reason=Direct actionability detected; Security/vulnerability signal; Dependency/ecosystem shift preview=Commit b21c419 by Daniel Han: Studio: fall back to text-only when llama.cpp is too old for a model's vision projector (#
- PURGE score=0 source=GitHub_openai-python reason=No significant markers found preview=Commit 7198756 by stainless-app[bot]: release: 2.41.1
- PROMOTE score=5 source=GitHub_openai-python reason=Security/vulnerability signal preview=Commit a526ee8 by Justin Beckwith: build: fix release workflow permissions (#3389)
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 5286e6e by Henning Dieterichs: Fixes builtin markdown editor paths
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit 1d7f9b5 by danielhanchen: Installer: never plan a non-sm_120 CUDA build on Blackwell, never plan CPU on an NVIDIA
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit 1d9090f by pre-commit-ci[bot]: [pre-commit.ci] auto fixes from pre-commit.com hooks  for more information, see ht
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit 0f00bc1 by Lee Jackson: Studio: fix Gemma-4-12B-it not loading (#6054)  * Fix Studio Python, Gemma 4 Unified side
- PURGE score=0 source=GitHub_unsloth reason=No significant markers found preview=Commit c86872c by danielhanchen: Merge #6156: never plan a non-sm_120 CUDA build on Blackwell, never plan CPU on an NVID
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit 2b319e8 by oobabooga: Studio: support separate-file MTP GGUF drafters (Gemma 4) (#6125)  * Studio: support separa
- PROMOTE score=10 source=GitHub_unsloth reason=Direct actionability detected; Security/vulnerability signal preview=Commit 8bca7bc by Michael Han: Studio: accept audio files through Add photos & files and fix the audio gate for Gemma 4 
- PROMOTE score=16 source=GitHub_unsloth reason=Direct actionability detected; Security/vulnerability signal; Dependency/ecosystem shift; Convergence detected preview=Commit cc1a724 by oobabooga: Source llama.cpp prebuilts from unslothai/llama.cpp (CUDA, ROCm, macOS) (#5963)  * Studio: 
- PURGE score=0 source=GitHub_unsloth reason=No significant markers found preview=Commit 18d851b by Daniel Han: Studio: mascot images degrade gracefully instead of showing alt text (#6146)  * Studio: ma

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
