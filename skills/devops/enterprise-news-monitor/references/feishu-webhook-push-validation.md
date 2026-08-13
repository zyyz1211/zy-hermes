# Feishu webhook push validation for enterprise briefings

Use this when manually pushing an enterprise observation/monitoring briefing to a Feishu group via a custom group robot webhook.

## Key lessons

- Prefer the Feishu **custom group robot webhook** for one-way briefing pushes when the task is “推送到飞书群”. Do not assume Hermes gateway `send --to feishu` is the right path.
- Hermes Feishu app delivery requires a real Feishu `chat_id`/`open_id`. If `FEISHU_HOME_CHANNEL` is actually an app id-like value (for example starts with `cli...`) or otherwise not a chat id, `hermes send --to feishu` can fail with:
  - `[230001] Your request contains an invalid request parameter, ext=invalid receive_id`
- A machine may contain multiple historical Feishu webhook URLs. Validate candidates before sending the real briefing. Old URLs may return:
  - `code=19001`, `msg=param invalid: incoming webhook access token invalid`
- Treat webhook URLs and access tokens as secrets. Do not print them in final answers or skill notes.

## Validation pattern

1. Build the message text and save it under the user’s tools/scripts directory, e.g. `Desktop/09_工具脚本/weekly_enterprise_observation_YYYYMMDD.txt`.
2. If a webhook URL is not in `.env`, search likely local history/log sources for Feishu custom robot URLs, but never reveal the URL:
   - `~/.hermes/.hermes_history`
   - `~/.hermes/logs/agent.log`
3. Deduplicate candidate URLs.
4. Send a short harmless connectivity test to each candidate and accept only `code == 0` / `msg == success`.
5. Push the real message to the validated candidate.
6. Report only the response status (`code=0, msg=success`) and the output file path; do not expose the webhook.

## Payload shape

```json
{
  "msg_type": "text",
  "content": {
    "text": "message text with real newline characters"
  }
}
```

Use Python `json.dumps(..., ensure_ascii=False)` to preserve Chinese text and handle newline escaping safely.
