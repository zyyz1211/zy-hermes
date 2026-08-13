#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enterprise News Search Script — uses Tavily Search API.
Reads TAVILY_API_KEY from environment variable (configured in .env).

Features:
- Searches each enterprise via Tavily basic depth (best relevance)
- Extracts dates from content via regex
- Filters low-relevance results by score + keyword check
- Outputs structured text for cron job agent consumption

Customize COMPANIES list below for your target enterprises.
"""

import subprocess, json, os, html, re
from datetime import datetime, timezone, timedelta

# === CONFIG: Customize your target enterprises here ===
COMPANIES = [
    "湖北宜化",
    "中国某大型能源集团",
    "某能源集团集团",
    "新和成",
    "某化纤集团",
    "富海控股",
]

TAVILY_URL = "https://api.tavily.com/search"
API_KEY = os.environ.get("TAVILY_API_KEY")
if not API_KEY:
    print("ERROR: TAVILY_API_KEY environment variable not set")
    print("Run: hermes config set TAVILY_API_KEY your_key")
    exit(1)

TZ = timezone(timedelta(hours=8))
now = datetime.now(TZ)
weekdays = "一二三四五六日"

print(f"每日企业信息监测 | {now.year}年{now.month}月{now.day}日 星期{weekdays[now.weekday()]}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

total = 0

for company in COMPANIES:
    print(f"【{company}】")

    payload = json.dumps({
        "api_key": API_KEY,
        "query": f"{company} 最新消息 {now.year}",
        "search_depth": "basic",
        "max_results": 5,
        "include_answer": False,
    })

    try:
        r = subprocess.run(
            ["curl", "-s", "--connect-timeout", "10", "--max-time", "20",
             TAVILY_URL, "-H", "Content-Type: application/json", "-d", payload],
            capture_output=True, text=True, timeout=25
        )

        if r.returncode != 0 or not r.stdout.strip():
            print("  搜索请求失败")
            print()
            continue

        data = json.loads(r.stdout)
        results = data.get("results", [])

        if not results:
            print("  暂无重大消息")
            print()
        else:
            for i, item in enumerate(results[:5]):
                title = html.unescape(item.get("title", "").strip())
                content = html.unescape(item.get("content", "").strip())
                url = item.get("url", "")
                score = item.get("score", 0)

                if not title or len(title) < 5:
                    continue

                # Filter: if title doesn't contain company name AND score is low, skip
                if company[:2] not in title and score < 0.5:
                    # Check if content mentions the company name or related terms
                    context = (title + " " + content)[:200]
                    keywords = [company[:2], "集团", "石化", "化工", "能源", "新材料",
                                "水电", "工程", "投资", "项目"]
                    if not any(kw in context for kw in keywords):
                        continue

                # Extract dates from content
                date_info = ""
                full_text = content[:300]
                dm = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", full_text)
                if dm:
                    date_info = dm.group(0)
                else:
                    dm = re.search(r"(\d{1,2})月(\d{1,2})日", full_text)
                    if dm:
                        # Check it's a reasonable date (not the company founding date, etc.)
                        month, day = int(dm.group(1)), int(dm.group(2))
                        if month <= 12 and day <= 31:
                            date_info = dm.group(0)
                if not date_info:
                    dm = re.search(r"(\d{4})-(\d{2})-(\d{2})", full_text)
                    if dm:
                        date_info = dm.group(0)

                if title:
                    clean = re.sub(r'\s+', ' ', content).strip()[:180]

                    print(f"  {i+1}. {title}")
                    if date_info:
                        print(f"     [日期] {date_info}")
                    print(f"     {clean}")
                    print(f"     {url}")
                    total += 1

    except json.JSONDecodeError:
        print("  数据解析失败")
    except subprocess.TimeoutExpired:
        print("  请求超时")
    except Exception as e:
        print(f"  错误: {str(e)[:80]}")

    print()

print(f"共检索到 {total} 条相关信息")
