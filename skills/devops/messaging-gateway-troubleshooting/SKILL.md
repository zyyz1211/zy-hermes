---
name: messaging-gateway-troubleshooting
description: Troubleshoot Hermes messaging gateway channels (Feishu/Lark, Telegram, API server, webhook) when external pushes or bot messages receive no response.
version: 1.1.0
created_by: agent
metadata:
  hermes:
    tags: [hermes, gateway, messaging, feishu, lark, telegram, webhook, troubleshooting]
---

# Messaging Gateway Troubleshooting

Use this skill when a user says a message sent through a bot/platform produced no reaction, e.g. "飞书机器人推送的任务没反应", "Telegram bot silent", "webhook sent but no reply", or "gateway channel stopped responding".

## Core diagnosis loop

1. **Check whether the gateway is actually running first.**
   - Windows native Hermes from MSYS/Git Bash may need the venv executable directly:
     ```bash
     '/c/Users/<user>/.hermes/hermes-agent/.venv/Scripts/hermes.exe' gateway status
     ```
   - `cmd.exe /c hermes ...` may print only the Windows banner in MSYS if quoting/interactive behavior goes sideways; prefer the full venv `hermes.exe` path for verification.

**CRITICAL: `hermes gateway status` can be misleading.** It only checks the PID file points to a running process. The gateway may be a **zombie** — the process exists but is not serving (port not listening, platforms not connected). Always follow up `status` with a service-level check.

1.5 **Verify the gateway is truly serving.** Do NOT stop at "status says running".
   ```bash
   # Check the API server port is actually listening
   netstat -ano | grep 8642
   # or on WSL/Linux:
   ss -tlnp | grep 8642

   # Hit the health endpoint — this is the definitive alive check
   curl -s --max-time 5 http://127.0.0.1:8642/health

   # Check the last few lines of gateway.log for a recent successful startup
   tail -20 ~/.hermes/logs/gateway.log
   ```
   - If `curl /health` fails (connection refused / timeout) and `netstat` shows no listener on 8642, the gateway is dead even if `status` claims it's running.
   - Kill the stale PID and restart: `taskkill /F /PID <n>` then `hermes gateway run`.
   - Restarted gateway should show `✓ <platform> connected` lines in log tail within 10-15s.

2. **Check gateway logs for the platform name and adapter errors.**
   - Primary logs:
     - `~/.hermes/logs/gateway.log`
     - `~/.hermes/logs/agent.log` (some gateway output may land here in TUI-spawned/manual runs)
     - `~/.hermes/logs/errors.log`
   - Look for: `Starting Hermes Gateway`, `Connecting to <platform>`, `✓ <platform> connected`, `No adapter available`, `failed to connect`, `Port ... already in use`, dependency install lines, and platform-specific warnings.

3. **Separate three failure classes.**
   - **Gateway not running**: start it, then verify readiness in logs.
   - **Platform adapter unavailable**: install/fix the missing dependency or credential; then restart gateway.
   - **Platform connected but messages ignored**: inspect routing rules (group mention requirement, allowlist, bot-message policy, home channel, topic/thread/session behavior).

4. **Verify with real log output before telling the user it is fixed.**
   - Do not stop at "installed" or "started". Confirm a line like:
     ```text
     Connecting to feishu...
     [Feishu] Connected in websocket mode (feishu)
     ✓ feishu connected
     Gateway running with N platform(s)
     ```

## Feishu/Lark robot no-response checklist

1. Confirm the gateway is truly serving (step 1.5 above), not just "status says running".
2. Confirm credentials are present (mask values; only report present/missing):
   - `FEISHU_APP_ID`
   - `FEISHU_APP_SECRET`
   - for webhook mode: `FEISHU_VERIFICATION_TOKEN` or `FEISHU_ENCRYPT_KEY`
3. Confirm required dependency is importable in the Hermes venv:
   ```bash
   '/c/Users/<user>/.hermes/hermes-agent/.venv/Scripts/python.exe' - <<'PY'
   import importlib.util
   print(importlib.util.find_spec('lark_oapi'))
   PY
   ```
4. If dependency is missing, install into the Hermes venv (use a mirror if needed):
   ```bash
   '/c/Users/<user>/.hermes/hermes-agent/.venv/Scripts/python.exe' -m pip install lark-oapi -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
   ```
5. Verify credentials against Feishu OpenAPI without printing secrets:
   - POST `/open-apis/auth/v3/tenant_access_token/internal`; success is `code=0`.
   - GET `/open-apis/bot/v3/info` with the tenant token; success proves the app credentials are valid and reveals the bot name/open_id for testing/mention gating (report the bot name, never tokens).
6. **Verify Feishu API permissions are actually working** by listing chats:
   ```bash
   # Get tenant_access_token first, then:
   curl -s -H "Authorization: Bearer $TOKEN" \
     "https://open.feishu.cn/open-apis/im/v1/chats?page_size=5"
   ```
   - Expected: `code=0` with a list of chats. If `code=99991663` ("permission denied"), the app lacks `im:chat` scope.
   - Seeing chats with valid names confirms `im:chat`, `im:message`, and bot scope are operative.
   - The bot can access DM chats and groups it has been added to.
7. For a controlled inbound test, temporarily relax local gates before restarting gateway:
   - `FEISHU_ALLOW_ALL_USERS=true`
   - `FEISHU_GROUP_POLICY=open`
   - `FEISHU_CONNECTION_MODE=websocket`
   - keep `FEISHU_REQUIRE_MENTION=true` for group tests, but **test DM first** to avoid mention/group-policy ambiguity.
8. Start/restart the gateway and verify Feishu connection lines in logs. Note: `hermes gateway restart` may stop a manual gateway then prompt to install the service and leave it stopped; if status says not running, start explicitly with `hermes gateway run` (background is okay for a long-lived daemon) and re-check status/logs.
9. If Feishu is connected but still silent, distinguish **no inbound event** from **inbound event rejected/ignored**:
   - Ask the user to send a fresh **DM** to the bot first (e.g. `测试`) and reply "已发". Then immediately search logs for `Inbound ... message received`, `Received raw message`, `dropping inbound event`, `Unauthorized`, `not authorized`, `send`, `reply`, and Feishu/Lark errors around the exact timestamp.
   - If there is **no** inbound Feishu message/event log after a known DM test, do not keep tuning local allowlists first: the event is not reaching Hermes. Check Feishu Developer Console permissions/events/version publishing.
   - Required Feishu permissions/events for normal chat: `im:message`, `im:message:send_as_bot`, `im:resource`, `im:chat`, `im:chat:readonly`, and event subscription `im.message.receive_v1`.
   - After changing Feishu permissions/events, publish a new app version in **Version Management** and complete any enterprise/admin approval; saved permission/event edits do not necessarily take effect until published.
   - Only after DM works, test groups by `@机器人` because Feishu group handling may require mention by default.
   - If the sender is another bot/automation, check bot-message policy such as `FEISHU_ALLOW_BOTS` / platform settings; Hermes may ignore bot-originated messages to prevent loops.
   - Check allowlists: `FEISHU_ALLOWED_USERS`, `FEISHU_ALLOW_ALL_USERS`, group policy, and per-group rules.

## Common pitfalls

- **`hermes gateway status` can report a zombie process.** The PID file may point to a pythonw.exe that's still alive but no longer serving (API port not listening, platform connections dropped). Always verify with a port check (`netstat -ano | grep 8642`) and health endpoint (`curl http://127.0.0.1:8642/health`). If the port is gone, the gateway is dead — kill the stale PID and restart.
- **Duplicate gateway processes fight over Feishu app_id.** If a gateway restart attempt fails because "another gateway already using this Feishu app_id (PID N)", the old PID N is the active one. If that PID later dies (check `tasklist`), the PID file may point to a different stale PID. Always check the process table explicitly.
- **Do not confuse outbound notification bots with inbound Hermes gateway.** A Feishu "robot push" may mean either (a) a Feishu message sent to the Hermes bot, or (b) a generic webhook/subscription event. Diagnose the actual transport: Feishu platform adapter vs Hermes webhook platform.
- **Gateway status can be stale/incomplete if multiple manual processes exist.** If status reports multiple PIDs, inspect logs and avoid spawning duplicate gateways with the same app credentials.
- **TUI/manual gateway runs may put SDK logs in the tracked background process, not only `gateway.log`.** For Feishu/Lark WebSocket churn, use `process(action='log', session_id=...)` when the gateway was started with `terminal(background=True, ...)`; Lark SDK lines such as `connected to wss://...`, `disconnected`, and `receive message loop exit` may appear there even when `~/.hermes/logs/gateway.log` only shows other platform reconnect spam.
- **A watch pattern like `connected` also matches `disconnected`.** When monitoring gateway output, avoid broad patterns or expect false notifications; prefer explicit final status checks and logs. If the monitor is noisy, kill the Hermes-tracked background wrapper with `process(action='kill', session_id=...)` only after verifying the actual gateway process/service remains running via `hermes gateway status`.
- **Redact Feishu/Lark WebSocket URLs before reporting.** Lark SDK connection lines include sensitive query parameters (`access_key`, `ticket`, `device_id`, `conn_id`). Replace them with `[REDACTED]` in user-facing output and stored references.
- **Feishu WebSocket disconnects are not automatically fatal.** Short `receive message loop exit, err: no close frame received or sent` followed by `trying to reconnect` and then `connected` is usually transient network/DNS churn. Treat it as unhealthy only if there is no later `connected` or messages still fail end-to-end.
- **Telegram/API server failures may be unrelated.** One platform failing to connect does not necessarily block another if logs show `Gateway running with N platform(s)` and the target platform is connected.
- **Setup-state failures are not durable conclusions.** Capture and apply the fix (install dependency, set env var, restart), not a claim that the platform is broken.

## Reference files

- `references/feishu-no-response.md` — condensed session-derived checklist for Feishu robot no-response diagnosis and real log signatures.
- `references/feishu-websocket-reconnects.md` — how to interpret Lark WebSocket disconnect/reconnect logs and avoid noisy `connected` watch-pattern alerts.
- `scripts/verify-feishu-credentials.py` — self-contained script: checks Feishu credentials, bot activation status, and im:chat permission by listing accessible chats. Run as `python scripts/verify-feishu-credentials.py` after exporting FEISHU_APP_ID and FEISHU_APP_SECRET.
