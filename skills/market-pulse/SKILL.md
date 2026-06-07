# Skill: market-pulse

Fetch BTC, ETH, and SOL prices from Coinbase API, generate a chart, and post to the Telegram group every 30 minutes.

## Requirements

- Python with matplotlib installed
- Outbound HTTPS access to api.exchange.coinbase.com
- A Telegram bot token with group access

## Implementation

1. Run `~/hermes/venv-market-pulse/bin/python ~/.hermes/scripts/market-pulse.py`
2. The script fetches prices, computes changes, fetches Fear & Greed index
3. Generates a matplotlib chart and sends it to Telegram

## Cron Setup

```bash
systemctl --user enable --now market-pulse.timer
```

## Troubleshooting

If the task gets rate limited (HTTP 429), the fix is to switch the model to DeepSeek V4 Flash paid tier. The script uses Hermes internally; if Hermes' model is still on free-tier Gemma, it will 429 every time.

## Verification

- Check the group 30 min after setup — chart + price summary should appear
- Check cron logs: `journalctl --user -u market-pulse -n 20`