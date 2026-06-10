# Noise Gate Context

_Generated: 2026-06-10 02:03:16 UTC_

## Last 24h

- PROMOTE: 56
- PURGE: 67
- Total: 123

## Top Reasons

- No significant markers found: 67
- Security/vulnerability signal: 42
- Direct actionability detected: 7
- Structural shift (engineering refactor/rewrite): 6
- Convergence detected: 5
- Dependency/ecosystem shift: 4

## Sources

- GitHub_vscode: 60
- GitHub_llama.cpp: 17
- GitHub_langchain: 15
- GitHub_ComfyUI: 13
- GitHub_unsloth: 11
- GitHub_ollama: 6
- GitHub_AutoGPT: 1

## Recent Decisions

- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit 46d45aa by Comfy Org PR Bot: chore(openapi): sync shared API contract from cloud@ca12913 (#14367)
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit 5ece24e by Talmaj: Depth anything 3 (Core-135) (#13853)  Co-authored-by: Alexis Rolland <alexisrolland@hotmail.co
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit 5fcf7a4 by comfyanonymous: Always enable cuda malloc on cu130 and higher. (#14381)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 271a21a by Rob Lourens: chat: use Copilot icon for Agent Host sessions in editor window (#320700)  * chat: use Co
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 3363bdb by Rob Lourens: chat: Include Copilot logs in Agent Host debug export (#320677)  * chat: include Copilot 
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 3113872 by Rob Lourens: Folder picker chip for Agent Host sessions in multi-root windows (#320681)  * Add Folder 
- PURGE score=0 source=GitHub_langchain reason=No significant markers found preview=Commit 77bbf8b by Mason Daugherty: test(langchain): mark legacy trigger view for 2.0 removal (#38002)  `SummarizationMid
- PROMOTE score=5 source=GitHub_langchain reason=Security/vulnerability signal preview=Commit 0f1b291 by Mason Daugherty: fix(core): type structured tool error handler output (#38003)  `handle_tool_error` ca
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit d3ccc49 by Martin Aeschlimann: Copilot AH: parse rules and other small parse fixes (#320662)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit c306c21 by Benjamin Christopher Simmonds: Merge pull request #320686 from microsoft/benibenj/cute-crocodile  Upda
- PROMOTE score=10 source=GitHub_vscode reason=Direct actionability detected; Security/vulnerability signal preview=Commit eaf41b7 by Don Jayamanne: chat: send agent host completion attachments (#320703)  * chat: send agent host complet
- PROMOTE score=9 source=GitHub_langchain reason=Structural shift (engineering refactor/rewrite); Security/vulnerability signal preview=Commit 8c5b36c by Mason Daugherty: fix(langchain): preserve summarization trigger compatibility (#38000)  `Summarization

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
