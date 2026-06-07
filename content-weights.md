# Content Weights & Rotation — Pulse Feed Engine

Every 5-min pulse or agent response picks content types based on weighted probability. Keeps the feed alive, varied, and context-appropriate without being predictable.

## Weight Table

| Content Type | Weight | Token Cost | Best Trigger |
|---|---|---|---|
| **Text provocation** | 🔥🔥🔥🔥🔥 | Free | Always present — every pulse has a text core |
| **Inline buttons** | 🔥🔥🔥🔥🔥 | Free | Every decision point |
| **Reaction MP4** | 🔥🔥🔥🔥🔥 | Free | Every completed item, every win |
| **Reaction GIF** | 🔥🔥🔥🔥 | Free | Fallback if MP4 unavailable |
| **Custom image** | 🔥🔥🔥🔥 | ~$0.01 | Milestones, new concepts, special moments |
| **Diagram** | 🔥🔥🔥 | Free (SVG) | Architecture changes, system explanations |
| **Poll** | 🔥🔥🔥 | Free | Decision points, vibe checks |
| **Music clip** | 🔥🔥 | ~$0.05 | Milestone celebrations, morning/late-night vibe |
| **Voice note** | 🔥🔥 | ~$0.01 | Story mode, morning greeting, sign-off |
| **Video clip** | 🔥 | ~$0.10 | Major milestones only |
| **PDF** | 🔥 | Free | Formal reports, sprint summaries |

## Contextual Trigger Map

| Event | Content Mix |
|---|---|
| **Task completed** | Text summary + Reaction MP4 + (10%: celebratory image) |
| **Decision needed** | Text prompt + Inline buttons + (10%: poll) |
| **Pulse cycle (normal)** | Text provocation + On-topic MP4 + Weighted constraint |
| **Special milestone** | Text + Custom image + Music clip + Reaction MP4 |
| **Blocked item** | Text flag + Thinking MP4 + Button: "reassign?" |
| **Signal promoted** | Text signal + Diagram + Reaction MP4 |
| **Sprint complete** | Full multi-format: image + music + MP4 + buttons |

## Implementation Rule

1. Every message starts with a text core (the substance)
2. Append exactly **one** secondary content type per message (don't spam)
3. Reaction MP4s are the default secondary for positive events
4. Buttons are the default secondary for decision events
5. Images/diagrams/music reserved for higher-signal moments

## Working MP4 IDs (Reaction Bank)

| Vibe | GIPHY ID |
|---|---|
| Celebration / fist pump | `1BhkfD0sfOBEHObDbc` |
| Lets go excitement | `hrEAdqXQJHJNhSiiMv` |
| Team USA hype | `JM5Ep9EeXGMyHVNraz` |
| Processing / thinking | `3oEjI6SIIHBdRxXI40` |