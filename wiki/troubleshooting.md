# Troubleshooting

## Agent Not Responding

1. Check gateway: `systemctl --user is-active openclaw-gateway.service` or `openclaw-nemoclaw.service`
2. Check Telegram connection: look for `[telegram] [default] starting provider (@botname)` in gateway logs
3. Check `requireMention` setting in the gateway config — if `true`, agent ignores non-@ messages
4. Check the model warmup in gateway logs: `startup model warmup failed` is non-fatal, gateway will try on-demand
5. Check auth: do they have an API key? For OpenClaw, check `agents/main/agent/auth-profiles.json` or `OPENROUTER_API_KEY` env var

## Gateway Fails to Start

```
Invalid config at ~/.openclaw/openclaw.json
```

Run: `openclaw doctor --fix` then restart

```
No API key found for provider "openrouter"
```

Create/open `agents/main/agent/auth-profiles.json` with:
```json
{"openrouter": {"apiKey": "sk-or-..."}}
```

Or use `EnvironmentFile=-%h/.hermes/.env` in the systemd service.

## Gateway Auth / Pairing Errors

If you see `gateway closed (1008): pairing required`:
1. Check `paired.json` in the devices directory
2. The agent trying to connect needs the right scopes: `operator.read`, `operator.write`, `operator.admin`, `operator.approvals`
3. If broken, write the scopes directly to `paired.json` and clear `pending.json`

## Agent Ghosting (Talks Then Goes Silent)

**Most common cause:** Provider-side instability on free-tier OpenRouter models. The model sends initial tokens then drops the connection.

**Fixes (in order):**
1. Clean restart: `systemctl --user restart openclaw-gateway.service`
2. Switch to a more stable model temporarily (Gemini Flash Lite often works when DeepSeek is unstable)
3. Check for rate limiting in the logs (`429`, `ETIMEDOUT`, `ECONNRESET`)

## Cron Jobs

All crons managed by Hermes. To check: `cronjob list` (tool). 
To pause a spammy cron: `cronjob action=pause job_id=xxx`
To manually trigger: `cronjob action=run job_id=xxx`

## Nemoclaw Sandbox Dead

If the nemoclaw Docker container is gone:
1. Try `nemoclaw nemoclaw-agent rebuild --yes`
2. If that fails with credential errors, the standalone gateway at ~/.openclaw-nemo is still running and working — the sandbox is optional