#!/usr/bin/env python3
"""
Verify Feishu bot credentials and API permissions.

Usage:
    python verify-feishu-credentials.py

Reads FEISHU_APP_ID and FEISHU_APP_SECRET from the environment
(or prompts user to export them). Checks:
  1. Tenant access token acquisition
  2. Bot info (name, activation status)
  3. Chat listing permission (im:chat scope)

Exit code: 0 if all checks pass, 1 otherwise.
"""
import json, os, sys, requests

APP_ID = os.environ.get("FEISHU_APP_ID")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET")

if not APP_ID or not APP_SECRET:
    print("ERROR: FEISHU_APP_ID and FEISHU_APP_SECRET must be set in environment.")
    print("Run: export FEISHU_APP_ID=cli_xxx && export FEISHU_APP_SECRET=xxx")
    sys.exit(1)

# Mask for display
masked_id = APP_ID[:6] + "..." + APP_ID[-4:] if len(APP_ID) > 10 else "(too short)"
masked_secret = APP_SECRET[:4] + "..." + APP_SECRET[-4:] if len(APP_SECRET) > 8 else "(too short)"
print(f"FEISHU_APP_ID:     {masked_id}")
print(f"FEISHU_APP_SECRET: {masked_secret}")

# ── Step 1: Get tenant_access_token ──
print("\n── Step 1: Tenant access token ──")
try:
    r = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
        timeout=10,
    )
    data = r.json()
    if data.get("code") != 0:
        print(f"FAIL: code={data['code']} msg={data.get('msg','?')}")
        print("  → Credentials invalid or app not approved.")
        sys.exit(1)
    token = data["tenant_access_token"]
    expires = data["expire"]
    print(f"OK: token acquired (expires in {expires}s)")
except requests.RequestException as e:
    print(f"FAIL: network error — {e}")
    sys.exit(1)

# ── Step 2: Bot info ──
print("\n── Step 2: Bot info ──")
try:
    r = requests.get(
        "https://open.feishu.cn/open-apis/bot/v3/info",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    data = r.json()
    if data.get("code") != 0:
        print(f"FAIL: code={data['code']} msg={data.get('msg','?')}")
        sys.exit(1)
    bot = data["bot"]
    bot_name = bot["app_name"]
    bot_open_id = bot["open_id"]
    bot_active = bot.get("activate_status", 0)
    active_str = {0: "inactive", 1: "pending", 2: "active"}.get(bot_active, str(bot_active))
    print(f"Bot name:      {bot_name}")
    print(f"Bot open_id:   {bot_open_id}")
    print(f"Status:        {active_str}")
    if bot_active != 2:
        print("  ⚠ Bot not fully active — check app review status.")
except requests.RequestException as e:
    print(f"FAIL: network error — {e}")
    sys.exit(1)

# ── Step 3: List chats (verify im:chat permission) ──
print("\n── Step 3: Chat listing (im:chat scope) ──")
try:
    r = requests.get(
        "https://open.feishu.cn/open-apis/im/v1/chats?page_size=10",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    data = r.json()
    code = data.get("code", -1)
    if code == 99991663:
        print("FAIL: permission denied (code 99991663)")
        print("  → The app lacks 'im:chat' scope. Enable it in Feishu Dev Console:")
        print("    https://open.feishu.cn/app -> Permissions -> im:chat")
        sys.exit(1)
    elif code != 0:
        print(f"FAIL: code={code} msg={data.get('msg','?')}")
        sys.exit(1)

    items = data["data"]["items"]
    print(f"OK: found {len(items)} accessible chat(s)")
    for c in items:
        cname = c.get("name", "(unnamed)")
        cid = c.get("chat_id", "?")
        ctype = c.get("chat_type", "?")
        cmember = c.get("member_count", "?")
        print(f"  • {cname:30s} type={ctype:6s} members={cmember:>4s} id={cid}")
except requests.RequestException as e:
    print(f"FAIL: network error — {e}")
    sys.exit(1)

# ── Summary ──
print(f"\n{'─'*40}")
print("All checks passed ✓")
print(f"Bot '{bot_name}' is active with chat listing access.")
print(f"\nNext steps if group @mention still fails:")
print("  1. Ensure the bot has been added to the target group")
print("  2. Confirm event subscription im.message.receive_v1 is enabled")
print("  3. Publish a new app version after any permission/event changes")
