# Noise Gate Context

_Generated: 2026-06-09 20:19:57 UTC_

## Last 24h

- PROMOTE: 65
- PURGE: 81
- Total: 146

## Top Reasons

- No significant markers found: 81
- Security/vulnerability signal: 49
- Dependency/ecosystem shift: 10
- Structural shift (engineering refactor/rewrite): 8
- Convergence detected: 8
- Direct actionability detected: 6

## Sources

- GitHub_vscode: 46
- GitHub_llama.cpp: 27
- GitHub_unsloth: 20
- GitHub_ComfyUI: 18
- GitHub_langchain: 13
- GitHub_ollama: 11
- GitHub_openai-python: 10
- GitHub_AutoGPT: 1

## Recent Decisions

- PROMOTE score=5 source=GitHub_langchain reason=Security/vulnerability signal preview=Commit 0f45b2c by Nidhi Rajani: feat(openai): support `apply_patch` built-in tool (#37157)  [Docs](https://github.com/la
- PURGE score=0 source=GitHub_langchain reason=No significant markers found preview=Commit c7d01d5 by Mason Daugherty: release(openai): 1.3.0 (#37989)
- PROMOTE score=9 source=GitHub_vscode reason=Structural shift (engineering refactor/rewrite); Security/vulnerability signal preview=Commit 21c5fff by Ladislau Szomoru: Agent Host - adopt changesets breaking changes (#320636)  * Bring over the latest ve
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit ad56489 by Kohaku-Blueleaf: Ensure conditions are not trainable to avoid bugs (#14368)
- PROMOTE score=5 source=GitHub_llama.cpp reason=Security/vulnerability signal preview=Commit 76da245 by Rémy Mathieu: webui: implement pinned conversations support (#21387)  * webui: implement pinned conver
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 50b471b by Megan Rogge: Run background terminal notifications on the conversation model (#320639)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 4b47f07 by Megan Rogge: xterm@6.1.0-beta.285 (#320646)  Diff: https://github.com/xtermjs/xterm.js/compare/6.1.0-b
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 99dcaab by Martin Aeschlimann: Skills contributed by VS Code Client do not contain descriptions (#320644)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 07f2a8a by Martin Aeschlimann: Avoid fetching chat modes on menu bar update (#320609)  * Avoid fetching chat mode
- PROMOTE score=13 source=GitHub_vscode reason=Direct actionability detected; Security/vulnerability signal; Dependency/ecosystem shift preview=Commit f8a5597 by Connor Peet: Kill full server process tree in agent host kill_running_server (#320631)  * Kill full se
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 8ed18a4 by Megan Rogge: Fix Rerun Task closing/removing one of the terminals (#320432)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 5c9d3ec by Tyler James Leonhardt: Revert "Add context size picker for Claude Agent models" (#320614)  Revert "Add

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
