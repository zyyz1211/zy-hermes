# Feishu/Lark WebSocket reconnect logs

Use this reference when Hermes gateway is running Feishu/Lark in WebSocket mode and the user receives repeated background notifications containing `connected` / `disconnected` lines.

## What the log patterns mean

Typical transient churn:

```text
[Lark] ... [ERROR] receive message loop exit, err: no close frame received or sent [conn_id=...]
[Lark] ... [INFO] disconnected to wss://msg-frontier.feishu.cn/ws/v2?...access_key=...&ticket=... [conn_id=...]
[Lark] ... [INFO] trying to reconnect for the 1st time
[Lark] ... [INFO] connected to wss://msg-frontier.feishu.cn/ws/v2?...access_key=...&ticket=... [conn_id=...]
```

Interpretation:
- `receive message loop exit, err: no close frame received or sent` usually means the WebSocket closed without a clean close frame; it is not fatal by itself.
- `trying to reconnect` followed by `connected` means the SDK recovered.
- `connect failed ... Failed to resolve 'open.feishu.cn'` points to DNS/network churn. Verify DNS/HTTPS separately before changing app credentials.
- If the last Lark line is `disconnected` and no later `connected` appears, treat Feishu as currently suspect and ask the user to run an end-to-end message test while checking logs.

## Verification sequence

1. Check Hermes gateway status:
   ```bash
   '/c/Users/<user>/.hermes/hermes-agent/.venv/Scripts/hermes.exe' gateway status
   ```
2. If the gateway was started with `terminal(background=True, watch_patterns=[...])`, inspect the tracked process log; Lark SDK output may be there rather than in `gateway.log`:
   ```python
   process(action='log', session_id='<proc_id>', limit=120)
   ```
3. Confirm whether there is a later `connected` after every `disconnected`.
4. Verify network if DNS errors appear:
   ```powershell
   Resolve-DnsName open.feishu.cn
   Invoke-WebRequest -UseBasicParsing -Method Head -TimeoutSec 10 https://open.feishu.cn
   ```
   A 404 from the root/HEAD still proves DNS and TLS connectivity; it is not a Feishu credential failure.
5. Ask for an end-to-end private message or group `@机器人` test. Connection-level success is not the same as message routing success.

## Watch-pattern pitfall

A watch pattern of `connected` matches both `connected` and `disconnected`, because `disconnected` contains the substring. This causes scary but misleading alerts.

Safer approaches:
- Do not use a broad `connected` watch pattern for Lark gateway runs.
- Prefer `notify_on_complete=True` for bounded tasks, or no watch pattern for long-running gateways.
- If already noisy, kill only the Hermes-tracked background wrapper with `process(action='kill', session_id=...)`, then immediately verify `hermes gateway status` so the real gateway was not stopped.

## Redaction requirement

Before reporting or saving logs, redact sensitive query parameters from Lark WebSocket URLs:

- `access_key=[REDACTED]`
- `ticket=[REDACTED]`
- `device_id=[REDACTED]`
- `conn_id=[REDACTED]`

Never paste raw WebSocket URLs containing those values into final replies or persistent skills.
