# Noise Gate Context

_Generated: 2026-06-10 10:54:20 UTC_

## Last 24h

- PROMOTE: 62
- PURGE: 65
- Total: 127

## Top Reasons

- No significant markers found: 65
- Security/vulnerability signal: 50
- Structural shift (engineering refactor/rewrite): 8
- Dependency/ecosystem shift: 8
- Direct actionability detected: 8
- Convergence detected: 6

## Sources

- GitHub_vscode: 63
- GitHub_langchain: 20
- GitHub_unsloth: 18
- GitHub_ComfyUI: 15
- GitHub_llama.cpp: 10
- GitHub_AutoGPT: 1

## Recent Decisions

- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit a8af864 by Sandeep Somavarapu: fix setting active session when new session is submitted (#320743)
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit f542ffb by Michael Han: Studio: unify shadows, backgrounds and dark mode consistency in chat UI (#6116)  * Studio
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 05b0388 by BeniBenj: remove second rename
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 7d5f746 by Benjamin Christopher Simmonds: Merge pull request #320728 from microsoft/benibenj/specified-rabbit  Re
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 959a2d1 by Lucas Parzianello: Fixed typo in cli update (#245751)  fixed typo in cli update  Co-authored-by: Lucas
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit d086ffe by Alexandru Dima: speed up vscode work tree flows (#320729)
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit 87deee7 by Daniel Han: Studio: faithful conversation export and import round trips (ShareGPT system role, CSV quo
- PROMOTE score=13 source=GitHub_unsloth reason=Direct actionability detected; Security/vulnerability signal; Dependency/ecosystem shift preview=Commit f41617a by Daniel Han: Studio: auto-sync allowScripts pins after dependency bumps (#6136)  * Studio: npm v12 read
- PROMOTE score=13 source=GitHub_unsloth reason=Direct actionability detected; Security/vulnerability signal; Dependency/ecosystem shift preview=Commit 5f622f6 by Matt Van Horn: fix: clearer Studio setup error when GPU driver is too old for the installed CUDA toolk
- PROMOTE score=10 source=GitHub_unsloth reason=Direct actionability detected; Security/vulnerability signal preview=Commit 3307561 by Daniel Han: Studio: npm v12 readiness for install-script gating (#6128)  npm 12 (July 2026) stops runn
- PURGE score=0 source=GitHub_unsloth reason=No significant markers found preview=Commit 4d2f29f by Michael Han: Studio: center account avatar vertically in sidebar footer pill (#6026)  Co-authored-by: 
- PROMOTE score=5 source=GitHub_unsloth reason=Security/vulnerability signal preview=Commit 256d17e by Darshan Poudel: fix(studio): block arbitrary external image URLs in markdown renderer (#5602)  * fix(s

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
