# Noise Gate Context

_Generated: 2026-06-12 04:18:47 UTC_

## Last 24h

- PROMOTE: 72
- PURGE: 79
- Total: 151

## Top Reasons

- No significant markers found: 79
- Security/vulnerability signal: 54
- Dependency/ecosystem shift: 22
- Convergence detected: 10
- Structural shift (engineering refactor/rewrite): 9
- Direct actionability detected: 8

## Sources

- GitHub_vscode: 64
- GitHub_unsloth: 48
- GitHub_langchain: 16
- GitHub_llama.cpp: 10
- GitHub_ComfyUI: 8
- GitHub_ollama: 3
- GitHub_AutoGPT: 1
- GitHub_openai-python: 1

## Recent Decisions

- PROMOTE score=5 source=GitHub_langchain reason=Direct actionability detected preview=Commit 5d20596 by Mason Daugherty: style(core,langchain,langchain-classic,partners): replace double backticks in docstri
- PURGE score=0 source=GitHub_langchain reason=No significant markers found preview=Commit f6d63bc by Mason Daugherty: release(langchain): 1.3.8 (#38096)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit d1e225f by Megan Rogge: Integrate Copilot Voice conversation engine (#320785)
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit 6dae2f5 by Daniel Han: Stop false RoPE 'default' warning and fix rope drift gate on transformers 5 (#6223)  * Han
- PURGE score=0 source=GitHub_unsloth reason=No significant markers found preview=Commit 0793775 by Michael Han: Fix kwarg spacing in training files to satisfy pre-commit (#6209)  The ruff-format-with-k
- PURGE score=0 source=GitHub_unsloth reason=No significant markers found preview=Commit 11d5f64 by Daniel Han: Studio: reword the Cloudflare line when the public probe fails (#6217)  On a 0.0.0.0 bind 
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit 84b42c9 by Leo Borcherding: fix: deduplicate lemonade ROCm prebuilt selection log (#6021)  * fix: deduplicate lem
- PROMOTE score=3 source=GitHub_unsloth reason=Dependency/ecosystem shift preview=Commit fb56b82 by oobabooga: Studio: fix llama.cpp update banner offering a downgrade / sticking on mix releases (#6219)
- PROMOTE score=3 source=GitHub_vscode reason=Dependency/ecosystem shift preview=Commit 158e9ed by dependabot[bot]: Bump shell-quote from 1.8.1 to 1.8.4 in /extensions/copilot/chat-lib (#321068)  Bumps
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 834cfc1 by dileepyavan: build: separate TSA product pipeline configuration (#321060)  * build: share product pipe
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit e8be393 by Kyle Cutler: Browser: adjust input coordinates for emulation scaling (#321065)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 588cbae by Justin Chen: clean up open agents window flow (#321038)  * clean up open agents window flow  * show pr

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
