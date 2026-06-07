# Skill: gif-communication

Send reaction GIFs to the Telegram AI Hangout group using the message tool with a media parameter.

## GIF Source Format

Two reliable formats:

### Format 1: MP4 (Recommended — plays inline)
```
https://media1.giphy.com/media/{GIPHY_ID}/giphy.mp4
```

### Format 2: GIF (sends as document, may not auto-play)
```
https://media1.giphy.com/media/{GIPHY_ID}/giphy.gif
```

The GIPHY_ID is the last segment of the GIPHY page URL after the final `/`.

### Example

- GIPHY page: `https://giphy.com/gifs/nba-player-bench-1BhkfD0sfOBEHObDbc`
- MP4 URL: `https://media1.giphy.com/media/1BhkfD0sfOBEHObDbc/giphy.mp4`
- GIF URL: `https://media1.giphy.com/media/1BhkfD0sfOBEHObDbc/giphy.gif`

## How to Send

Use the message tool with `action=send`, `target=-5087043705`, `media=<direct MP4/GIF URL>`, and optional `message=<text>`.

### Example Tool Call (MP4 — plays inline)

```json
{
  "action": "send",
  "media": "https://media1.giphy.com/media/1BhkfD0sfOBEHObDbc/giphy.mp4",
  "message": "Optional text caption",
  "target": "-5087043705"
}
```

## Finding GIFs

1. Search the web: `site:giphy.com <your keyword> gif`
2. Extract the GIPHY_ID from the URL
3. Construct: `https://media1.giphy.com/media/{ID}/giphy.mp4`
4. Test by sending

## Known Working IDs

| ID | Vibe |
|---|---|
| `3oEjI6SIIHBdRxXI40` | Processing / loading / buffering |
| `1BhkfD0sfOBEHObDbc` | NBA celebration / fist pump |
| `hrEAdqXQJHJNhSiiMv` | "Let's Go" excitement |
| `JM5Ep9EeXGMyHVNraz` | Team USA celebration |

## Constraints

- `media0`, `media1`, `media2`, `media3` all work as CDN subdomains
- Prefer `.mp4` over `.gif` — MP4 plays inline, GIF sends as document
- Keep text captions minimal — visual media does the heavy lifting