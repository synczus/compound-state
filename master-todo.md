# Compound Session — Todo & Status

## ✅ Done This Session

- [x] **Aggressive mode enabled** — SOUL.md + initiation-protocol v3 set to "Execute First, Ask Never"
- [x] **Kairos joined AI Hangout** — fixed channel_directory.json (was missing the group)
- [x] **STT fixed (all 3 gateways)** — swapped whisper from `large-v3` (3GB, CPU-dead) → `tiny` (150MB, 0.3s cached) on Hermes/Kairos/Shannon
- [x] **Pipeline HUNAA-18** — transitioned to in_progress, CEO ran briefly, then cancelled and parked
- [x] **Pipeline agent heartbeats** — all 5 turned OFF
- [x] **OpenRouter meter** — `or-meter.sh` script + cron every 30 min posting bar to chat

## 🔴 Needs Attention

- [ ] **Kairos & Shannon not posting to group** — both bots receive messages and generate responses, but "Suppressing normal final send" blocks delivery. Session key collision — bots share `agent:main:` prefix. Need to fix session key isolation or clear state.db
- [ ] **Whisper upgrade** — "crisp audio, best there is" — wire up OpenAI or Groq Whisper for all agents once API keys are available (local tiny works but accuracy is mid)
- [ ] **OpenRouter meter cap** — Chase bumped the daily limit, need the new value to update `kestrel/meter/config.json`

## 📋 Session Summary

| Topic | Status |
|-------|--------|
| Aggressive autonomy | ✅ Live |
| Kairos/Shannon in chat | 🔴 Session key fix needed |
| STT transcription | ✅ Working (tiny) |
| Pipeline | ⏸️ Parked |
| OR meter | ✅ Every 30 min |
| Budget | Bumped — new value TBD |