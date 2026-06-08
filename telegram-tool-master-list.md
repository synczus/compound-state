# Telegram Tool Master List
## AI Hangout — Compound Control Center

**Vision:** Telegram is the remote control. Every tool, every API, every service is reachable from this chat. You say it, the compound does it.

---

## Setup Order (Priority: High → Low)

### P0: Already Running (Zero Setup)

| Tool | What It Does | How to Use |
|---|---|---|
| **Image Generation** | Generate any image from a prompt | Say "design X" → image posts to chat |
| **Music Generation** | Create audio/beats | Say "make a beat" → audio posts |
| **Diagram Maker** | Architecture/flow diagrams | Say "draw the system" → SVG in PDF |
| **PDF Generator** | Any doc as PDF | Say "make a PDF of X" |
| **Web Search** | Internet research | Say "search for X" or just ask |
| **DuckDB Pipeline** | 14,586 scored signal events | Queries run against trading signals |
| **Perplexity Feeder Cron** | Auto-generates research prompts | Every 30 min, posts JSONs to this chat |
| **AgentMemory** | Persistent cross-session memory | 263 functions, 53 MCP tools, viewer :3113 |

### P1: Needs API Key (Can Wire in <10 Min)

| # | Tool | What It Adds | Needs From You | Est. Time |
|---|---|---|---|---|
| 1 | **Make.com** | Bridges 2,000+ tools visually (Figma→Telegram, Canva→Telegram, Sheets→Telegram, etc.) | Make.com account (free) | 10 min |
| 2 | **Canva Connect API** | Auto-generates branded designs from chat — fill templates, export PDF/PNG | Canva API key | 10 min |
| 3 | **Figma Webhooks** | Design updates auto-post to AI Hangout ("Dashboard_v2 was updated") | Figma access token + file/team/context ID | 10 min |
| 4 | **NotebookLM API** | Drop a URL/PDF → research summary + audio podcast back in chat | Google API access | 15 min |
| 5 | **Google Sheets API** | Read/write spreadsheets from chat ("Log that trade", "What's in the tracker?") | Google API service account | 15 min |
| 6 | **GitHub Issues API** | Create/read issues from Telegram ("Bug: Striker offline") | GitHub PAT | 5 min |

### P2: Needs API Keys + Minor Config (Already Built, Sitting in kestrel/execution/)

| # | Tool | Lines | What It Adds | Needs From You |
|---|---|---|---|---|
| 7 | **Freqtrade (Coinbase)** | 356 | Buys/sells coins on regulated US exchange | Coinbase API key |
| 8 | **Bybit Futures** | 258 | Basis arbitrage, works sideways markets | Bybit API key |
| 9 | **MMR Bridge (IBKR)** | 197 | IBKR execution via MMR protocol | 4 IBKR credentials |
| — | **Dual Supervisor** | 178 | Manages all 3 above with budget guard | Auto-enabled when keys arrive |

### P3: Needs Build (Compound-Native)

| # | Idea | What It Does | Effort |
|---|---|---|---|
| 10 | **Design Pipeline** | "Design a Kestrel logo" → Canva/Figma/Image gen auto-picks best tool | 30 min |
| 11 | **Research Pipeline** | Drop URL → NotebookLM + web_search → summary + podcast → posts back | 30 min |
| 12 | **Auto-Trader** | Pipeline signals → DuckDB → execution stacks → trades | Ready, just needs keys |
| 13 | **Gauntlet Game** | One agent breaks something, others fix it in 3 min. Timer in AI Hangout | 1 hr |
| 14 | **Weekly Report** | Every Sunday: read pipeline → fill Canva template → post PDF to group | 1 hr |
| 15 | **Pulse Monitor** | Monitors Striker/WolfWatch/budget/25+ sources, auto-alerts on red | 30 min |
| 16 | **Design by Voice** | Say spec → compound generates dashboard mockup from AgentMemory rules | 2 hr |

---

## The Architecture

```
TELEGRAM CHAT (AI Hangout)
    |
    ├── Compound Agents (Kairos/Nemoclaw/Hermes/Shannon/Kestrel)
    │       ├── AgentMemory (persistent memory ~ localhost:3111)
    │       ├── DuckDB (signal database)
    │       └── Synapse Dashboard (port 19888)
    │
    ├── Make.com (bridges 2,000+ tools)
    │       ├── Figma Webhooks → Telegram
    │       ├── Canva Connect API → Telegram
    │       ├── Google Sheets → Telegram
    │       └── NotebookLM → Telegram
    │
    └── Execution Layer (sitting ready)
            ├── Freqtrade (Coinbase) — 356 lines
            ├── Bybit Futures — 258 lines
            └── MMR Bridge (IBKR) — 197 lines
```

---

## The Goal

One chat. 20+ tools. Design, research, trading, data, automation, monitoring — all reachable from AI Hangout.

You say: "Design a Kestrel dashboard, dark theme"
Compound: Generates in Canva, exports to PDF, posts back, stores in AgentMemory for next session.

You say: "Give me next week's plan for the compound"
Compound: Reads current state → generates in Canva → posts PDF report.

You say: "What's happening in the market?"
Compound: Queries DuckDB → generates summary → posts to chat.

All from one thread. Zero context switching.

---

*Last updated: 2026-06-07 21:30 ET*
*Authored by Nemoclaw — reviewed by Hermes, Kairos, Shannon*