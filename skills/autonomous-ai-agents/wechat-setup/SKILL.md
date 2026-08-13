---
name: wechat-setup
description: Connect Hermes Agent to WeChat (Weixin) via iLink Bot API — QR scan login, message relay, and gateway integration.
version: 1.0.0
---

# WeChat (Weixin) Setup via iLink Bot

## Overview

Connect Hermes Agent to WeChat using the iLink Bot API. This enables the agent to send and receive WeChat messages through the messaging gateway.

## Key Concepts

- **account_id**: The iLink bot identity, e.g. `xxx@im.bot`
- **user_id**: The WeChat user ID, e.g. `<wechat_user_id>...@im.wechat`

## Setup Steps

1. Create an iLink bot and obtain the account_id.
2. Configure the messaging gateway with the bot credentials.
3. Scan the QR code to log in.
4. Verify message relay works.

## Notes

- iLink bot identities (`xxx@im.bot`) typically cannot receive group messages.
- The user ID format is `<wechat_user_id>@im.wechat`.
