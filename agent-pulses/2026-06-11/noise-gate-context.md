# Noise Gate Context

_Generated: 2026-06-11 23:41:44 UTC_

## Last 24h

- PROMOTE: 76
- PURGE: 79
- Total: 155

## Top Reasons

- No significant markers found: 79
- Security/vulnerability signal: 59
- Dependency/ecosystem shift: 19
- Convergence detected: 13
- Structural shift (engineering refactor/rewrite): 11
- Direct actionability detected: 9
- Asymmetry/Contrarian signal detected: 2

## Sources

- GitHub_vscode: 63
- GitHub_unsloth: 44
- GitHub_langchain: 22
- GitHub_ComfyUI: 12
- GitHub_llama.cpp: 10
- GitHub_ollama: 2
- GitHub_AutoGPT: 1
- GitHub_openai-python: 1

## Recent Decisions

- PROMOTE score=5 source=GitHub_ComfyUI reason=Security/vulnerability signal preview=Commit 10d466b by comfyanonymous: Don't crash when using flux kv cache with split batches. (#14422)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 8f6555f by Sandeep Somavarapu: check also if authenticatin provider is registered (#321042)
- PROMOTE score=5 source=GitHub_ollama reason=Security/vulnerability signal preview=Commit f8a48df by Parafee41: llm: decouple prompt caching from context shift (#16639)  This PR separates prompt caching 
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 0eec4e3 by Vijay Upadya: Fix missing CLI session tool calls and agent response in agent debug logs (#321024)  * F
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit f6b248c by Karthik Nadig: Enhance WebPageLoader for markdown content extraction (#320146)  * feat: enhance WebPag
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit befc321 by Jedrzej Kosinski: Make --enable-manager-legacy-ui imply --enable-manager (#14421)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 33d8e5a by Martin Aeschlimann: Fix 'Canceled Failed to load custom agents' message in logs (#320986)
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 16c85da by Justin Chen: fix inline editing input not haveing full width (#321031)  * fix inline editing input not
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit f9070ac by Logan Ramos: Improve the local to native and remote to local copy, paste, and DND experience (#320685)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit a3634cd by Connor Peet: Wire up MCP App support for agent-host sessions (#321016)  * working, in theory  * finish
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 55fbd4a by Benjamin Christopher Simmonds: Merge pull request #320981 from microsoft/benibenj/open-newt  Don't tog
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 112a911 by Alexandru Dima: sessions: fix race where in-flight Claude session is spuriously removed (#321017)  * F

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
