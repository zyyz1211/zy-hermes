# Feishu robot no-response diagnosis

Session-derived durable pattern for Hermes gateway troubleshooting.

## Observed symptoms

- User sends/forwards a task through a Feishu robot and sees no response.
- `hermes gateway status` can show the gateway is not running, or logs show Feishu adapter was skipped.

## Useful real log signatures

Old/broken state:

```text
✗ Gateway is not running
Feishu: lark-oapi not installed or FEISHU_APP_ID/SECRET not set
No adapter available for feishu
```

Fixed/healthy Feishu state:

```text
Connecting to feishu...
[Feishu] Connected in websocket mode (feishu)
✓ feishu connected
Gateway running with 2 platform(s)
```

A non-target platform may fail independently; for example Telegram timeout does not prove Feishu is broken if Feishu shows connected:

```text
telegram connect timed out
✓ feishu connected
```

## Commands that worked on Windows native Hermes from MSYS/Git Bash

Use the Hermes venv executables directly to avoid `cmd.exe /c hermes` interactive/banner oddities:

```bash
'/c/Users/<user>/.hermes/hermes-agent/.venv/Scripts/hermes.exe' gateway status
'/c/Users/<user>/.hermes/hermes-agent/.venv/Scripts/python.exe' -m pip install lark-oapi -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
'/c/Users/<user>/.hermes/hermes-agent/.venv/Scripts/hermes.exe' gateway run
```

## After Feishu connects but still no response

- In Feishu groups, ask the user to test with an explicit `@机器人` mention.
- If the event originates from another bot/automation, inspect `FEISHU_ALLOW_BOTS` or equivalent adapter settings because bot-originated messages may be ignored to prevent loops.
- Check allowlists and group policies before assuming transport failure.
