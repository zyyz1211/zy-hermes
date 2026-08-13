---
name: wechat-setup
description: "Connect Hermes Agent to WeChat (Weixin) via iLink Bot API, including QR code login, pairing, and home channel configuration."
version: 1.0.0
author: Agent (created from session)
tags: [hermes, wechat, weixin, gateway, messaging, qr-code, windows]
---

# WeChat (Weixin) Setup for Hermes Agent

Connect Hermes Agent to your personal WeChat account using Tencent's iLink Bot API. This skill covers the full setup flow including the QR code login workaround for environments where terminal QR rendering fails (common on Windows).

## Prerequisites

- Hermes Agent installed and configured with a working model
- A WeChat account on your phone
- `aiohttp` and `cryptography` Python packages installed

```bash
pip install aiohttp cryptography
# Optional: for terminal QR rendering (recommended)
pip install qrcode[pil]
```

## Quick Start (3 steps)

```bash
# 1. Run the interactive setup wizard
hermes gateway setup

# 2. Select "Weixin / WeChat" (option 3)
# 3. Scan the QR code with your phone's WeChat
# 4. Credentials are saved to ~/.hermes/.env automatically
```

## Windows-Specific Workaround

On Windows, the `hermes gateway setup` subprocess may fail to render the QR code in the terminal even when `qrcode` is installed. This happens because the gateway subprocess resolves a different Python path than the one `qrcode` was installed into.

### Workaround Script

A reusable Python script is provided at `scripts/wechat_setup_qr.py`. It:

1. Pipes input to the interactive wizard (`3\ny\n` to select WeChat + confirm)
2. Captures the QR URL from stdout in real time
3. Generates a QR code image using Python's `qrcode` library
4. Saves the image to the desktop (`~/Desktop/wechat_qrcode.png`)
5. Auto-refreshes the image if the QR code expires
6. Waits for the user to scan and the setup to complete

```bash
python scripts/wechat_setup_qr.py
```

The user then opens the desktop image and scans it with WeChat.

## Post-Setup Steps

After the QR scan succeeds, you'll see:
```
微信连接成功，account_id=xxx@im.bot
```

### 1. Verify Credentials

```bash
grep WEIXIN ~/.hermes/.env
```

Expected output:
```
WEIXIN_ACCOUNT_ID=xxx@im.bot
WEIXIN_TOKEN=xxx@im.bot:token_string
WEIXIN_BASE_URL=https://ilinkai.weixin.qq.com
WEIXIN_CDN_BASE_URL=https://novac2c.cdn.weixin.qq.com/c2c
```

### 2. Set DM Policy

Choose one of these and add to `~/.hermes/.env`:

| Policy | Value | Behavior |
|--------|-------|----------|
| Pairing (recommended) | `WEIXIN_DM_POLICY=pairing` | User must pair first via `/pairing approve` |
| Open | `WEIXIN_DM_POLICY=open` | Anyone can message the bot |
| Allowlist | `WEIXIN_DM_POLICY=allowlist` + `WEIXIN_ALLOWED_USERS=id1,id2` | Only listed users |
| Disabled | `WEIXIN_DM_POLICY=disabled` | No DMs accepted |

### 3. Set Group Policy (recommended: disabled)

```bash
echo 'WEIXIN_GROUP_POLICY=disabled' >> ~/.hermes/.env
```

Note: iLink bot identities (`xxx@im.bot`) typically cannot receive group messages anyway.

### 4. Pair the User (if using pairing mode)

The user sends a message to the bot, then the gateway logs show:
```
WARNING gateway.run: Unauthorized user: <user_id> on weixin
```

Pair with:
```bash
hermes pairing approve weixin <pairing_code>
```

The pairing code is sent back to the user in WeChat by the bot.

### 5. Set Home Channel

The bot will prompt: "No home channel is set for Weixin." Set it via `.env`:
```bash
echo 'WEIXIN_HOME_CHANNEL=<user_id>' >> ~/.hermes/.env
```

Where `<user_id>` is the WeChat user ID (e.g. `<wechat_user_id>...@im.wechat`).

### 6. Start the Gateway

```bash
# Foreground (test)
hermes gateway run

# Background (production)
hermes gateway start
```

After starting, verify in the logs:
```bash
grep "weixin.*connected" ~/.hermes/logs/gateway.log
# → ✓ weixin connected
```

## PITFALLS

### QR code module not found by gateway subprocess

**Symptom:** `（终端二维码渲染失败: No module named 'qrcode'）` even though `pip list | grep qrcode` shows it installed.

**Root cause:** The gateway subprocess resolves a different Python than the one `qrcode` was installed under. On the user's system, `python` (3.13.2) has `qrcode` but `python3` (3.14.6) doesn't — the gateway may invoke either.

**Fix:** Install `qrcode[pil]` for both Pythons, or use the workaround script (see above) that generates the QR image via a known-good Python before the subprocess starts.

### Setup wizard stalls at interactive prompt

**Symptom:** The wizard shows the platform selection menu but doesn't advance.

**Fix:** Use piped input: `printf "3\ny\n" | hermes gateway setup`. The "3" selects Weixin, the "y" confirms QR login.

### QR code expires before user scans

**Symptom:** `二维码已过期，正在刷新... (1/3)` then the process exits.

**Fix:** The workaround script auto-refreshes. If using the raw wizard, the process auto-refreshes up to 3 times. Re-run if all 3 expire.

### "Unauthorized user" after gateway restart

**Symptom:** Pairing approval is lost on gateway restart.

**Fix:** If using `pairing` mode, the pairing persists across restarts — the approval is stored. If the user sees "Unauthorized user" on the SECOND message after restart, it means the pairing was stored on the previous session but the new gateway process hasn't loaded it. Send another message and it should work. If it persists, approve again.

## References

- [Hermes Agent Messaging Docs](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/)
- [WeChat (Weixin) Adapter Docs](https://hermes-agent.nousresearch.com/docs/zh-Hans/user-guide/messaging/weixin)
- `scripts/wechat_setup_qr.py` — The reusable QR code setup script
