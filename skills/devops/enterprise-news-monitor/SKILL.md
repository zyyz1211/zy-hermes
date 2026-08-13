---
name: enterprise-news-monitor
version: 1.6.0
description: "Set up automated daily enterprise news monitoring: search multiple enterprises via Tavily API → LLM analyze/rank → push curated briefing to Feishu (or other channels)."
triggers:
  - "企业新闻监测"
  - "每日信息推送"
  - "企业信息监测"
  - "enterprise news monitor"
  - "企业动态监控"
category: devops
---

# Enterprise News Monitor

Set up a daily cron job that searches news for a list of target enterprises via **Tavily Search API**, analyzes importance by LLM, and pushes a curated briefing to Feishu (飞书) group webhook.

## Architecture Options

### Option A: Single comprehensive daily briefing (original)
One cron job at 9AM that searches, analyzes, and pushes a full daily report covering all enterprises and all importance levels.

```
Cron job (0 9 * * 1-5) — every weekday at 9:00 AM
    │
    ├── Script: daily_news_search.py
    │       └── subprocess + curl → Tavily /search (basic depth, no time_range)
    │       └── stdout = formatted news text with dates → injected into agent prompt
    │
    └── LLM Agent (prompt)
            ├── 1. Analyze & rank by importance (🔴 important / 🟡 watch / 🟢 routine)
            ├── 2. Extract dates, key data points (amounts, percentages, timelines)
            ├── 3. Format as structured message
            └── 4. Push to delivery channel
```

### Option B: Multi-tier monitoring (recommended for 用户)
Two cron jobs sharing the same script + skills but different prompts:

| Job | Schedule | Behavior | Coverage |
|-----|----------|----------|----------|
| **Comprehensive daily briefing** | `0 9 * * 1-5` | Full report, all enterprises, all levels | 🔴🟡🟢 |
| **Important-only silent scanner** | `0 13,17 * * 1-5` | Only push if 🔴 important news found; otherwise output nothing | 🔴 only |

**Silent scan pattern**: The important-only cron job's prompt instructs the agent to output an empty string when no 🔴 news is detected. The `deliver` field still routes to the channel, but empty output means nothing is actually sent. This avoids noisy "nothing to report" messages.

### Option C: Webhook-driven alerts (NOT recommended without external trigger)
Hermes webhook can receive POSTs from external news monitoring services. However, **without an existing external trigger source, implementing webhook + self-polling is unnecessary complexity** — direct cron push is simpler and more reliable. 用户 rejected this approach as "不靠谱" (not practical). Only use webhook if you have a genuine external system that can POST news data to Hermes.

```bash
hermes webhook subscribe enterprise-alert
# External system POSTs to /webhooks/enterprise-alert
# Hermes processes and pushes to delivery channel
```

### Option D: Periodic Industry Research Report (e.g., 化工新建项目周报)

A weekly (rather than daily) report that tracks developments in a specific industry sector, using **web_search** (not Tavily API) with strict source quality requirements.

**Use case**: Industry-specific project tracking, competitive intelligence, sector trend analysis — where source authority and narrow time range matter more than multi-enterprise breadth.

**Key differences from Option A/B:**
| Dimension | Enterprise News Monitor (A/B) | Industry Research Report (D) |
|-----------|-------------------------------|------------------------------|
| Frequency | Daily (weekdays) | Weekly (e.g., every Friday) |
| Data source | Tavily API via script | web_search tool (LLM-driven) |
| Toolset | `[terminal]` | `[web, terminal, file]` |
| Scope | Multiple enterprises | Single industry sector |
| Source priority | Any verified news | Government > listed company > SOE > industry media |
| Delivery channel | Feishu | WeChat or Feishu |

**Source hierarchy (most authoritative first):**

1. **一级来源（优先使用）：**
   - 政府生态环境局环评公示（如 xx市生态环境局、省生态环境厅）
   - 上市公司公告（通过巨潮资讯网、上交所/深交所公告）
   - 央企/国企官方新闻（如 中国石油官网、中国石化新闻）
   - 公共资源交易平台/招标平台（如 宜昌公共资源交易电子服务系统）
   - 发改委/工信部项目备案信息

2. **二级来源（辅助使用，需标注"据xx报道"）：**
   - 权威财经媒体（证券时报、上海证券报、中国证券报）
   - 行业权威媒体（中国能源报、中国化工报、石油化工）
   - 地方人民政府官网

3. **禁止使用：**
   - 无来源的通用网络文章、自媒体拼凑内容
   - 无法追溯到具体政府/企业/公告的信息

**Time range: MUST be exactly 7 days.** The user explicitly rejected reports spanning nearly a month. Every search should target "近7天" / "本周" scope. Only include items with verified publication dates within the window.

**Per-item source attribution:** Every data point must cite a specific source name in the format `【来源：xx市生态环境局】` or `【来源：万华化学公告】`. Never omit the source.

**Recommended template structure:**

```text
标题：{N}个化工新建项目最新动态：{最重磅1-2个项目}领衔
本期周报时间范围：YYYY年M月D日 — M月D日

一、重点项目进展（大型炼化、烯烃、新材料、新能源材料）
- 每个项目2-3句话：项目概况 + 最新进展 + 投资额 + 来源
- 按重要性排序，突出百亿级/千亿级项目

二、其他项目进展（中小型新材料、精细化工、环保技改）
- 简要罗列，每个1句话
- 可分组（新材料/精细化工/环保技改）

三、本期项目动向解读
- 2-3段趋势分析，基于真实数据
- 关注：产业布局方向、投资热点、技术路线、区域分布

四、推荐阅读
- 3-5篇本周相关深度文章链接
```

**Search strategy (for web_search tool):**
- Target specific government sites: `site:gov.cn 化工 项目 环评`
- Search specific enterprises: `万华化学 公告 项目`, `中国石油 项目 开工`
- Search bidding platforms: `招标 化工 项目`
- Search industry media: `化工 项目 进展 本周`
- Always limit to recent time range in search queries

**Pitfall — WeChat rate limiting on cron delivery:**
The iLink Bot API (WeChat gateway backend) has a tight rate limit (`"iLink sendmessage rate limited; cooldown active for 30.0s"`) that can persist across repeated runs. If a weekly cron job consistently hits this, switch delivery to Feishu. See the "Delivery Channels → WeChat" section above for the migration path.

## Delivery Channels

### WeChat (微信) — direct cron delivery (⚠️ rate limited)

Cron jobs can push directly to WeChat by setting `deliver=weixin:<chat_id>`:

```bash
hermes cron create "0 9 * * 1-5" \
  --deliver "weixin:<wechat_user_id>@im.wechat"
```

The WeChat gateway must be running (`hermes gateway run`). No webhook needed — the cron agent's output is sent directly as a WeChat message. Set `WEIXIN_HOME_CHANNEL` in `.env` for cron/cross-platform message routing.

**⚠️ Persistent rate limiting**: iLink Bot API (WeChat gateway backend) has a tight rate limit that can block cron deliveries repeatedly. Observed behavior: `"iLink sendmessage rate limited; cooldown active for 30.0s"` — even after cooldown, repeated runs still fail. If a cron job consistently hits this error, the delivery channel is unreliable. **Fallback**: switch the job's `--deliver` target from WeChat to Feishu — the content generation completes successfully, only the delivery fails.

**Migration path when WeChat rate limits block delivery:**
1. Find the correct Feishu group chat_id in `channel_directory.json` (see Feishu section below)
2. Update the cron job: `cronjob action=update job_id=<id> deliver="feishu:oc_<chat_id>"`
3. Test with `cronjob action=run job_id=<id>`
4. Verify `last_delivery_error` is `null`

### Feishu (飞书) — two delivery modes

#### Mode 1: Cron direct delivery (recommended for daily pushes)
Set `--deliver feishu:oc_<chat_id>` on the cron job. The chat_id must be the **group chat ID** (starts with `oc_`), NOT the bot's app_id (`cli_...`):

```bash
hermes cron create "0 9 * * 1-5" \
  --deliver "feishu:oc_4044e0ea6015f5186cbbfbbfe2168225"
```

**Finding the correct chat_id**: Read `~/.hermes/channel_directory.json`:
```json
{
  "platforms": {
    "feishu": [
      {"id": "oc_4044e0ea6015f5186cbbfbbfe2168225", "name": "zyAgent天团", "type": "group"}
    ]
  }
}
```
Use the `id` field of the target group — it starts with `oc_` (open chat ID), NOT `cli_` (bot app ID).

**Caveat — "origin" delivery may not resolve**: Setting `deliver=origin` on a cron job does NOT always resolve to the session where the job was created. If the job was created from a WeChat session, `origin` targets WeChat (which is rate limited). Always use explicit `feishu:oc_<chat_id>` for reliable Feishu delivery.

**Verify delivery succeeded**: After `cronjob action=run`, check `last_delivery_error` is `null` and that `last_status` is `"ok"`.

#### Mode 2: Webhook push (one-off or manual pushes)

See the Feishu custom bot webhook section below for webhook-based Feishu delivery.

## Prerequisites

1. **Tavily API Key** — sign up at https://app.tavily.com
2. **Hermes web backend** set to tavily:
   ```
   hermes config set web.backend tavily
   hermes config set web.search_backend tavily
   hermes config set web.extract_backend tavily
   ```
3. **TAVILY_API_KEY** in `.env`:
   ```
   hermes config set TAVILY_API_KEY your_key_here
   ```
4. **Feishu group Webhook URL** — from group settings → 群机器人 → 自定义机器人

## Setup Steps

### 1. Create the search script

Copy `scripts/daily_news_search.py` to `~/.hermes/scripts/daily_news_search.py`.

The script:
- Reads `TAVILY_API_KEY` from environment (never hardcode)
- Uses `subprocess.run(["curl", ...])` for HTTPS requests (avoids Windows Python SSL exit 49 issue)
- Searches each enterprise via Tavily `/search` endpoint with `basic` depth
- Extracts dates from content field using regex
- Outputs formatted text for cron injection

### 2. Create the cron job

```bash
hermes cron create "0 9 * * 1-5" \
  --name "每日企业信息监测" \
  --prompt [analysis + push instructions] \
  --script daily_news_search.py \
  --enabled-toolsets terminal \
  --deliver local
```

Key parameters:
- `script` — data collection script; its stdout is injected into the agent prompt as context
- `enabled-toolsets: ["terminal"]` — only need terminal for curl push
- `deliver: local` — don't deliver cron output to chat (push is handled in prompt)

### 3. Prompt design

The cron prompt should instruct the agent to:

1. **Analyze** each news item from the injected script output
2. **Rank** by importance:
   - 🔴 Important — major project signing, capital events (bond/IPO), strategic cooperation, major policy impacts
   - 🟡 Watch — operational developments, tech innovation, new market entries, personnel changes
   - 🟢 Routine — general news, recruitment, daily updates, internal activities
3. **Extract dates** from each item — every item MUST have a date label
4. **Extract key data** — amounts (元), percentages, capacity (万吨/万千瓦), timelines, partner names
5. **Format** as structured Feishu message with `\n` newlines
6. **Push** via curl POST to webhook

### 4. Example push command

```bash
curl -s -X POST 'https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_URL' \
  -H 'Content-Type: application/json' \
  -d '{"msg_type":"text","content":{"text":"formatted content with \\n for line breaks"}}'
```

## Push Format Template

For 用户's enterprise monitoring, default to a **near-7-day readable briefing**, not a long-range strategic intelligence dump and not a field-by-field database record.

**Note on delivery channels:**
- **WeChat (iLink Bot)**: Supports Markdown natively — `#` headers, `**bold**`, emoji all render. Newlines can be literal `\n`.
- **Feishu**: Uses JSON webhook — `\\n` for newlines, no Markdown in text-type messages.

```
📰 近7日企业最新动态 | 6月16日(周二)

━━━━━━━━━━━━━━━━━━━━

🔴【重要】湖北宜化
标题（2026年6月16日）
→ 用1-2句话说明发生了什么、涉及哪些项目/合作方/关键数据、为什么值得关注。没有量化数据时写“公开信息未披露明确金额/产能等量化数据”。
👉 来源名：https://...

🟢【一般】新和成
近7日暂无通过核验的公开动态

━━━━━━━━━━━━━━━━━━━━
📊 近7日通过核验 N 条；已排除旧闻、招聘、百科/简介、股票行情/研报和栏目页
🧪 试运行：第X/3天，等待用户反馈口径和可读性
```

**Coverage rule: EVERY enterprise in the list must appear in the push.** If a company has no verified news in the last 7 days, write "近7日暂无通过核验的公开动态" — never skip it entirely and never pad with old/weak items.

## Pitfalls

### Cron Job Provider Drift

**Symptom**: A cron job scheduled at a specific time silently doesn't run, or `cronjob action=run` returns:
```
RuntimeError: Skipped to prevent unintended spend: global inference config drifted since this job was created (provider 'X' -> 'Y'), and this job is unpinned.
```

**Cause**: The global `config.yaml` model provider changed after the cron job was created. Unpinned jobs block execution on drift to prevent unintended spend against the wrong provider.

**Fix**: Pin the job to an explicit model + provider:
```bash
hermes cron update <job_id> --model deepseek --model-name deepseek-v4-flash
# Or via Hermes CLI:
cronjob action=update job_id=<id> model={"model":"deepseek-v4-flash","provider":"deepseek"}
```

**Prevention**: Always pin cron jobs at creation time:
```bash
hermes cron create "0 9 * * 1-5" \
  --model deepseek \
  --model-name deepseek-v4-flash \
  ...
```

Or update existing jobs to pin them. Pinned jobs survive config changes and re-deploys.

### Duplicate Gateway Instance

**Symptom**: Starting `hermes gateway run` fails with:
```
Port 8642 already in use
WARNING gateway.run: ✗ api_server failed to connect
ERROR: [Weixin] Weixin bot token already in use (PID 17284). Stop the other gateway first.
```

**Fix**: The gateway is already running (PID in the error message). Stop the duplicate attempt. To verify the running gateway:
```bash
# Windows: use tasklist to find the PID from the error
# Or just check if delivery works — if the gateway is running, cron delivery to WeChat/Feishu will work.
```

**Never start a second gateway instance** — only one can hold the WeChat bot token and Feishu websocket connection at a time.

### WeChat vs Feishu Delivery Format

- **WeChat (iLink Bot)**: Supports **Markdown natively** — `# headers`, `**bold**`, emoji like `🔴`, and literal `\n` newlines all render correctly. The cron agent's plain-text output with Markdown formatting is delivered as-is.
- **Feishu**: Uses JSON webhook (`msg_type: text` or `msg_type: post`). Text type does NOT support Markdown — use `\\n` (double-backslash-n) for newlines in the JSON payload. Rich content requires `post` or `interactive` msg_type.

If switching channels, update the delivery format accordingly. The same cron prompt that works for WeChat may produce broken formatting on Feishu (and vice versa).

### Silent Scan Pitfalls

- **Date/year validation is mandatory**: Always identify the year, not just month/day. For daily/weekly briefings, only use current-year items unless the user explicitly asks for historical context. Prefer items within the current date ±1-2 months; reject old-year same-month/day articles (e.g. a July 19 article from last year must not be reported as current). If a source omits the year, cross-check the article page, URL path, search metadata, or another source before including it; otherwise label it as uncertain and normally exclude it.
- **Publication date only — never historical/company attribute dates**: Do not treat dates near words like “成立于/创立于/注册成立/注册于/始建于/起源于/更名/总部位于” as news dates. Example failure to avoid: a recruitment page saying “公司成立于1998年3月18日” must not be output as “2026届校园招聘启动（1998年3月18日）”.
- **Recruitment and job pages are noise for strategic-customer monitoring**: Exclude 校园招聘/招聘/社招/岗位/职位/宣讲会/就业信息/招聘简章/到期时间 pages entirely, even if they mention the monitored company and current year.
- **Biography, company profile, and stock quote pages are also noise**: Exclude 百度百科/公司简介/工商信息/会员单位介绍 and stock quote/data pages (股价/股票/行情/报价/公告大全/个股数据/资金流向). These frequently contain stale or non-news dates.
- **Do not trust search snippet recency**: Search engines may surface old pages for current queries. Validate each candidate's publication date from the page itself or reliable metadata before ranking.
- **Windows Python SSL exit 49**: Python 3.13 on Windows has SSL issues for HTTPS requests. Always use `subprocess.run(["curl", ...])` for any HTTP calls from scripts, never `urllib.request` or `requests`.
- **DO NOT hardcode API keys** in the script. Read from env var (`os.environ.get("TAVILY_API_KEY")`).
- **Enterprise name ambiguity**: Common Chinese enterprise names frequently collide with unrelated entities. E.g. "某石化企业" matches "鸿海科技/冬海集团/新海" in search results. **Mitigation**: use the most specific name variant (e.g. "富海控股" instead of "某石化企业"), and filter by checking company name appears in title/content.
- **Coverage failures**: If the push prompt doesn't explicitly require covering ALL enterprises, the LLM may skip companies with thin results. **Always include** "每家企业必须覆盖，无新闻则写暂无重大消息" in the prompt.
- **Script file location**: Scripts must be in `~/.hermes/scripts/`. Relative paths in `--script` resolve there.
- **Cron job deliver=local**: The push is handled by the LLM agent in the prompt. `deliver=local` prevents the raw output from also being sent to the current chat.
- **⚠️ time_range parameter degrades relevance**: Using `search_depth: "advanced"` with `time_range: "week"` causes severe noise (unrelated results, spam, SEO garbage). Always use `search_depth: "basic"` (no time_range) for best relevance. The basic search returns high-quality results even if some are older.
- **⚠️ include_raw_content adds noise**: `raw_content` contains HTML/markup garbage. Script should only use `content` field (AI-summarized, clean text). For deeper context, extract key sentences from content rather than enabling raw_content.
- **⚠️ Feishu multi-line JSON escaping**: Feishu webhook expects `\n` (literal backslash-n) inside JSON strings for newlines. Python's `json.dumps()` does NOT auto-convert `\n` to `\\n` for JSON-in-JSON payloads. Build the text string with `\n` then `json.dumps()` the whole payload, or construct the curl -d argument manually.
- **Feishu group message format**: Text type messages support basic emoji but no markdown/bold/links. Rich content requires `post` or `interactive` msg_type with specific JSON structure.

## User Preference: Format & Detail Level (用户)

When pushing to the user (用户, 某工程集团经营管理部), whether via WeChat or Feishu:

1. **时间范围默认近7天** — the user's intended product is “企业最新动态”, not long-range background intelligence. For daily monitoring, only include news with a verified publication date within the last 7 days. Older items must be excluded unless the user explicitly asks for a wider lookback.
2. **每条必须标注完整日期/年份** — extract and verify dates from article content. Use `(YYYY年M月D日)` or `(M月D日，YYYY年)` notation when possible. If no reliable year is found, do not include it; never report last-year same-month/day news as recent.
3. **准确性是最高优先级** — strategic-customer monitoring is used for business decisions. 宁缺毋滥: do not include uncertain dates, weak company matches, recruitment/job pages, encyclopedia/company-profile pages, stock quote/market pages, broker research PDFs, or generic index/list pages. If confidence is low, exclude and show “近7日暂无通过核验的公开动态”.
4. **可读性优先** — Feishu push should read like a leadership briefing, not a database dump. Do not list every field mechanically. Write: title + date, then 1-2 natural-language sentences explaining what happened, key data/partner/project if any, why it matters, then source link. If no quantitative data is disclosed, say “公开信息未披露明确金额/产能等量化数据”; never invent data.
4. **每条必须有原文链接** — use `👉 https://...` format. Links are the minimum acceptable level of detail when content is thin. User said "实在不行给个链接".
4. **优先级标签** — use 🔴重要 / 🟡值得关注 / 🟢一般. Reserve 🔴 for: project signings, bond/IPO approvals, strategic cooperations, major policy impacts.
5. **简洁但有信息量** — each item should be 2-3 lines max: `title（date）` → `key data point` → `→ insight` → `👉 link`.
6. **全覆盖** — ALL enterprises in the monitoring list must appear in the push. If one has no news, write "暂无重大消息" — never omit it.
7. **飞书换行** — use `\n` (backslash-n) in JSON string for line breaks.

## Verification

After setup, test with:
```
hermes cron run <job_id>
```

Or manually test the pipeline:
```bash
cd ~/.hermes/scripts && python3 daily_news_search.py
# Then construct the Feishu push manually
```

Check the Feishu group for the pushed message. The first run may take 30-60 seconds due to Tavily API calls + LLM analysis.

### Manual push troubleshooting on this Windows Hermes host

When the user asks for an immediate Feishu push, prefer the Feishu **custom bot webhook** path for outbound briefings, not the Hermes gateway `feishu` adapter unless a valid `chat_id` has been confirmed.

Symptoms and handling:
- `hermes send --to feishu ...` returning `[230001] ... invalid receive_id` means `FEISHU_HOME_CHANNEL` is not a valid Feishu receive ID for message.create. Do not keep retrying gateway send; use the custom bot webhook or fix the home channel.
- Multiple webhook URLs may exist in logs/history. Validate with a harmless short test and require Feishu response `{"code":0,"msg":"success"}` before sending the full briefing.
- A Feishu response `19001 param invalid: incoming webhook access token invalid` means that webhook URL is stale/invalid; try another configured/recorded custom bot webhook or ask the user for the current one.
- Never print, store in memory, or include webhook URLs/tokens in the final answer. Report only `code=0, msg=success` or the sanitized error.

Example validation/send pattern (do not echo the URL):
```bash
python - <<'PY'
# -*- coding: utf-8 -*-
import json, subprocess
url = 'https://open.feishu.cn/open-apis/bot/v2/hook/...'  # keep secret
text = '飞书机器人连通性测试'
payload = json.dumps({'msg_type':'text','content':{'text':text}}, ensure_ascii=False)
r = subprocess.run(['curl','-sS','--connect-timeout','10','--max-time','30','-X','POST',url,'-H','Content-Type: application/json; charset=utf-8','-d',payload], capture_output=True, text=True, encoding='utf-8', errors='replace')
print(r.stdout)
PY
```

For one-way briefing pushes, prefer a validated Feishu custom group robot webhook over Hermes gateway `send --to feishu` unless a real Feishu `chat_id` is known. If multiple historical webhook URLs exist, send a short test first and only use a candidate returning `code=0` / `msg=success`; `code=19001` means the webhook token is invalid. See `references/feishu-webhook-push-validation.md`.

## Files

- `scripts/daily_news_search.py` — search script (customize COMPANIES list)
- `references/tavily-api.md` — Tavily Search API parameter reference
- `references/daoyi-7day-readable-briefing.md` — 用户纠正后的企业监测固定口径：近7日最新动态 + 可读简报 + 禁止项/推送格式
