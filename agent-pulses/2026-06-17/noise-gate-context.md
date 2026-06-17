# Noise Gate Context

_Generated: 2026-06-17 07:52:29 UTC_

## Last 24h

- PROMOTE: 22
- PURGE: 45
- Total: 67

## Top Reasons

- No significant markers found: 37
- Security/vulnerability signal: 16
- Temporal decay exceeded limit: 8
- Dependency/ecosystem shift: 8
- Direct actionability detected: 3
- Structural shift (engineering refactor/rewrite): 3
- Convergence detected: 2

## Sources

- GitHub_vscode: 13
- GitHub_llama.cpp: 11
- GitHub_ComfyUI: 10
- GitHub_langchain: 10
- GitHub_unsloth: 10
- GitHub_ollama: 7
- GitHub_openai-python: 6

## Recent Decisions

- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 1d14fc1 by dileepyavan: Protect terminal sandbox settings file (#321723)
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit d5376cf by kononnable: ci: fix vulkan docker images (#24595)  * Update vulkan-shaders-gen.cpp  * Update vulkan-sh
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 5e91f34 by Justin Chen: use feature rich model picker in panel chat (#321722)  * use feature rich model picker in
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit fffbc00 by Justin Chen: fix editing previous request in agents window not working (#321719)
- PROMOTE score=3 source=GitHub_ollama reason=Dependency/ecosystem shift preview=Commit 7ea692c by Jeffrey Morgan: llama: update llama.cpp to b9637 (#16609)
- PURGE score=0 source=GitHub_ollama reason=No significant markers found preview=Commit 993acc7 by Jeffrey Morgan: model: update lfm2 parser/renderer for optional thinking (#16359)
- PURGE score=0 source=GitHub_ollama reason=No significant markers found preview=Commit bbb40a0 by Jeffrey Morgan: server: context shift for context windows larger than 8k, add error when hitting conte
- PROMOTE score=3 source=GitHub_ollama reason=Dependency/ecosystem shift preview=Commit 9e4ed74 by Patrick Devine: integration: look for the "hf" tool in integration tests (#16765)  The "huggingface-cl
- PURGE score=0 source=GitHub_ollama reason=No significant markers found preview=Commit 0f047fe by Jeffrey Morgan: llm: context shift allow shiftable prompts (#16764)
- PURGE score=0 source=GitHub_ollama reason=No significant markers found preview=Commit acfb50d by Jeffrey Morgan: models: add cohere2_moe (Command A / North) to the MLX engine (#16670)  Implements Coh
- PROMOTE score=3 source=GitHub_ollama reason=Dependency/ecosystem shift preview=Commit 8c432fc by Patrick Devine: llama: update llama.cpp to b9672 (#16775)
- PROMOTE score=3 source=GitHub_llama.cpp reason=Dependency/ecosystem shift preview=Commit 02810c7 by Oliver Simons: Fix and restrict NVFP4 edge-cases in llama-graph (#24331)  * Move post-GEMM MUL require

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
