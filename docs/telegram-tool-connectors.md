# Telegram Tool Connectors

Goal: Telegram bot with API hands in every direction — design, research, data, deploy, monitor, automate.

## STATUS KEY

- ✅ **Wired** — running, configured
- ⏳ **Pending key** — needs API key from Chase
- 🚧 **Needs setup** — needs Chase to create account/plan
- 📋 **Planned** — designed by Perplexity, ready to build

---

## TIER 1 — Ship First (Highest Leverage)

### 1. Canva Connect API ⏳
- **What**: Headless design generation from brand templates (Autofill)
- **How**: "design [thing]" → agent picks template → fills text/images → exports → posts to group
- **Need**: Canva Enterprise plan + API key from developer console
- **Pattern**: Brand template with fields (text, images) → POST /autofills → poll → export

### 2. n8n 🚧
- **What**: Self-hosted workflow engine (like Zapier, but ours)
- **How**: Docker container, web UI to wire ANY API to ANY API
- **Pattern**: Telegram hook → n8n → [Canva / Google Sheets / email / Slack / etc.]
- **Setup**: `docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n`
- **Takes**: ~5 min

### 3. Google Flows ⏳
- **What**: Native Workspace automation with Gemini AI
- **How**: "weekly signal summary to Telegram" — agent triggers Flows workflow
- **Need**: Google Workspace account (Standard/Plus tier for Gemini)

---

## TIER 2 — Utility Workhorses

### 4. YouTube Data API ⏳
- **What**: Fetch transcripts, analyze video content
- **How**: "analyze this video" → fetch transcript → summarize → post
- **Need**: Google Cloud project + YouTube API key
- **Setup**: One API key, copy-paste into .env

### 5. Google Drive API ⏳
- **What**: Read/write files from Telegram
- **How**: "save that to Drive" / "pull the latest trading plan"
- **Need**: Google Cloud project + OAuth credentials

### 6. Vercel / Hostinger API 🚧
- **What**: Deploy sites from Telegram
- **How**: "deploy this dashboard" → push → Vercel builds → preview URL posted
- **Setup**: Create account, add API token to .env

---

## TIER 3 — Nice-to-Haves

### 7. Cloudflare Workers ⏳
- **What**: Serverless endpoints, webhook transforms
- **How**: Trigger from Telegram for transforms, redirects, small APIs
- **Need**: Cloudflare account + API token

### 8. GitHub Actions ✅
- **What**: Run workflows from Telegram
- **How**: "run the deploy workflow" — already works via MCP
- **Status**: Wired into Kairos

### 9. Supabase 🚧
- **What**: Postgres + auth + realtime
- **How**: "run this query" from Telegram if we move beyond DuckDB
- **Setup**: Create project, add API key

### 10. Spotify API ⏳
- **What**: Control music from Telegram
- **How**: "play lofi" → pick playlist → play
- **Need**: Spotify Dev account + OAuth

### 11. Twitter/X API ⏳
- **What**: Monitor mentions, tweet from Telegram
- **How**: "what's trending in crypto" → post thread
- **Need**: X Developer account (paid tier for write access)

---

## ALREADY WIRED (Don't Touch)

| Tool | Status | Notes |
|---|---|---|
| **AgentMemory** | ✅ Running | :3111, systemd, boot-persistent |
| **AI Image Gen** | ✅ Built-in | image_generate tool |
| **Perplexity** | ✅ Auto-query gen | Every 30 min, 10 queries |
| **Diagrams/SVG** | ✅ Built-in | diagram-maker skill |
| **Music Gen** | ✅ Built-in | music_generate tool |
| **DuckDB** | ✅ Running | Signal pipeline |
| **FreqTrade** | ✅ Running | :8081, paper mode |
| **MMR Adapter** | ✅ Running | Poll mode, 60s |

---

## HOLDING (Needs Infra/Decision)

| Tool | Blocked On |
|---|---|
| **CryptoQuant** | API key (0.89 signal baseline) |
| **Figma** | Read-only API, needs plugin for writes |
| **NotebookLM** | No public API (web-fetch only by agents) |

---

## Quickest Wins Right Now

1. **n8n** (5 min, no account needed) — starts gluing everything together immediately
2. **YouTube API** (10 min, one API key) — unlocks video analysis
3. **GitHub Actions** (already wired) — already working, use more
4. **Canva** — when you have Enterprise, one API key unlocks the whole design pipeline
