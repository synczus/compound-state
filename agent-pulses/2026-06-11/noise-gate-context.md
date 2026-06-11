# Noise Gate Context

_Generated: 2026-06-11 00:20:33 UTC_

## Last 24h

- PROMOTE: 86
- PURGE: 59
- Total: 145

## Top Reasons

- Security/vulnerability signal: 75
- No significant markers found: 59
- Dependency/ecosystem shift: 16
- Direct actionability detected: 12
- Structural shift (engineering refactor/rewrite): 10
- Convergence detected: 9

## Sources

- GitHub_vscode: 51
- GitHub_unsloth: 49
- GitHub_langchain: 26
- GitHub_ComfyUI: 10
- GitHub_llama.cpp: 6
- GitHub_openai-python: 2
- GitHub_AutoGPT: 1

## Recent Decisions

- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit fccd1c7 by Connor Peet: Merge pull request #320854 from microsoft/connor4312/agent-host-mcp-integration  MCP serv
- PROMOTE score=14 source=GitHub_ComfyUI reason=Direct actionability detected; Structural shift (engineering refactor/rewrite); Security/vulnerability signal preview=Commit ce200c0 by Matt Miller: feat(assets): include asset id in executed WebSocket message (#13862)  * feat(assets): en
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 1b50e88 by Sandeep Somavarapu: add logs for setting manifest (#320599)  * add logs for setting manifest  * fix co
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 1a8e7a4 by Rob Lourens: Filter subagent sessions out of listSessions (#320835)  Subagent child sessions are regis
- PURGE score=0 source=GitHub_langchain reason=No significant markers found preview=Commit f0a78bf by Mason Daugherty: test(anthropic): make tests robust to gateway base URL (#38043)  Anthropic unit tests
- PROMOTE score=3 source=GitHub_langchain reason=Dependency/ecosystem shift preview=Commit 007ae66 by Mason Daugherty: test(anthropic): make expected warnings explicit (#38044)  Warning-producing test pat
- PURGE score=0 source=GitHub_langchain reason=No significant markers found preview=Commit 21eeadf by Mason Daugherty: test(partners): account for warning behavior in partner tests (#38046)  Partner unit 
- PROMOTE score=9 source=GitHub_ComfyUI reason=Structural shift (engineering refactor/rewrite); Security/vulnerability signal preview=Commit e5b7140 by Matt Miller: feat(assets): add job_ids filter to GET /api/assets (#13998)  * feat(assets): add job_ids
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 254ae50 by dileepyavan: Restrict GPG sandbox permissions for chained commands (#320858)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit b49826f by Courtney Webster: Merge pull request #320666 from microsoft/dull-lion  Update enterprise strings for U
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 4ab1d98 by Aaron Munger: add env var to AH to tag our CAPI traffic (#320814)  * add env var to AH to tag our CAPI
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 9df626d by Connor Peet: Merge pull request #320712 from microsoft/connor4312/314149  agentHost: fix client tool a

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
