# Noise Gate Context

_Generated: 2026-06-14 15:45:36 UTC_

## Last 24h

- PROMOTE: 7
- PURGE: 15
- Total: 22

## Top Reasons

- No significant markers found: 15
- Security/vulnerability signal: 6
- Dependency/ecosystem shift: 2
- Direct actionability detected: 1

## Sources

- GitHub_llama.cpp: 9
- GitHub_vscode: 5
- GitHub_ComfyUI: 4
- GitHub_unsloth: 4

## Recent Decisions

- PROMOTE score=10 source=GitHub_unsloth reason=Direct actionability detected; Security/vulnerability signal preview=Commit da3f7ac by oobabooga: Studio: add temporary (incognito) chat (#5956)  * Studio: add temporary (incognito) chat  *
- PURGE score=0 source=GitHub_ComfyUI reason=No significant markers found preview=Commit 5897d0c by Alexander Piskun: [Partner Nodes] feat(Tripo3d): add new "Import 3D" node (#14466)  Signed-off-by: big
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit 1fd6dfe by Amos Wong: ui : fix ui clipping in mobile due to incorrect height setup (#24605)
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit acd79d6 by Sigbjørn Skjæret: jinja : add count/d/e filter aliases (#24606)
- PROMOTE score=8 source=GitHub_unsloth reason=Security/vulnerability signal; Dependency/ecosystem shift preview=Commit f372da4 by DoubleMathew: MLX Training updates (#5656)  * Expose MLX grad value clipping in Studio  * update test 
- PROMOTE score=3 source=GitHub_unsloth reason=Dependency/ecosystem shift preview=Commit 19ae073 by Daniel Han: Studio: clarify llama.cpp update banner copy (#6313)  Rename the banner heading from "New 
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit 6e14286 by Michael Wand: cli : fix not copying preserved tokens (#24258)
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit 8ed274e by Bartowski: Add cohere2moe to llama-vocab for TINY_AYA (#24601)
- PROMOTE score=5 source=GitHub_vscode reason=Security/vulnerability signal preview=Commit 4ac5322 by Daniel Imms: fix(terminal): track ligatures addon config for change detection (#318992)  Store ILigatu
- PURGE score=0 source=GitHub_llama.cpp reason=No significant markers found preview=Commit 4672211 by Sigbjørn Skjæret: ci : use CUDA label for cuda backend (#24594)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit 9b43a71 by RedCMD: fix: Restrict continue comment to whitespace separated slashes (#321230)
- PURGE score=0 source=GitHub_vscode reason=No significant markers found preview=Commit c25b323 by Kyle Cutler: Browser: fix URLs incorrectly matching file:// scheme (#321302)

## Agent Use

- Use PROMOTE/PURGE ratios to avoid repeating dead signal patterns.
- If a source is repeatedly purged, demand stronger evidence or actionability.
- If a reason repeatedly promotes, preserve that marker in future routing.
