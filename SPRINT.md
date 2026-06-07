# Kestrel Markets — SPRINT.md
## Sprint: Stateful Background Hunter (Inversion Loop #1)

### Status: VERIFIED

## Achieved
- [x] Multi-repo GitHub Commit Hunter (10 high-signal repos)
- [x] Stateful dedup via SQLite (no redundant signal processing)
- [x] Engineering-aware NoiseGate (structural shift, security, dependency detection)
- [x] AutoHOP v2.2 pointer protocol integration (Perplexity -> Gemini -> Gemma)
- [x] CLI: pipeline, poll, hunt, state, targets commands
- [x] End-to-end verified: 6/10 llama.cpp commits promoted through Hub

## Current Bottleneck (Inversion Finding #1)
**Rate-limit starvation + single-repo tunnel vision** -> SOLVED via multi-repo + stateful polling.

## Current Bottleneck (Inversion Finding #2)
**Engineering signal novelty**: The "fix" keyword is too broad. Many commit messages contain "fix" (build fix, doc fix, UI fix). This inflates scores without true asymmetry. 
**Proposed fix**: Increase specificity — require "fix" + "security" or "fix" + "crash"/"vulnerability" to score in the security category.

## Next Inversion: Async Poller Deployment
- Seed all 10 repos via `python main.py pipeline`
- Set up cron-based background poller (`python main.py poll` via cronjob)
- Add rate-limit telemetry (track remaining requests via X-RateLimit-Remaining header)
- Replace mock specialist calls with real OpenRouter/Ollama calls

## Target: Complete Autonomous Signal Feed
The system should run continuously, consuming < 55 GitHub API requests/hour, feeding high-leverage engineering signals to the Hub autonomously.

## Targets Registered
1. ggerganov/llama.cpp - Local LLM inference shifts
2. nomic-ai/gpt4all - Local LLM ecosystem
3. ollama/ollama - Local LLM orchestration
4. autogpt/AutoGPT - Autonomous agent shifts
5. Significant-Gravitas/AutoGPT - Autonomous agent shifts (canonical)
6. comfyanonymous/ComfyUI - Local image gen infrastructure
7. langchain-ai/langchain - LLM orchestration framework
8. microsoft/vscode - Dev tool ecosystem shifts
9. openai/openai-python - API ecosystem changes
10. unslothai/unsloth - Fine-tuning optimization