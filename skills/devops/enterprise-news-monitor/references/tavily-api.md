# Tavily Search API Reference

## Endpoint

```
POST https://api.tavily.com/search
Content-Type: application/json
```

## Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | required | Your Tavily API key |
| `query` | string | required | Search query string |
| `search_depth` | string | `"basic"` | `"basic"` (faster, better relevance) or `"advanced"` (more results, more noise) |
| `max_results` | int | 5 | Max results to return (1-20) |
| `include_answer` | bool | false | Include AI-generated answer summary |
| `include_raw_content` | bool | false | Include full raw page content (HTML) |
| `include_domains` | array | [] | Only search these domains |
| `exclude_domains` | array | [] | Exclude these domains |
| `time_range` | string | null | `"day"`, `"week"`, `"month"`, `"year"` — **WARNING**: causes severe quality degradation with `advanced` depth |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `results[].title` | string | Article title |
| `results[].url` | string | Source URL |
| `results[].content` | string | AI-summarized content excerpt (clean text) |
| `results[].score` | float | Relevance score 0-1 |
| `results[].raw_content` | string|null | Full page content (HTML, only if `include_raw_content=true`) |
| `response_time` | float | API response time in seconds |
| `request_id` | string | Unique request identifier |

## Critical Learnings (from production use)

### 1. Never use `time_range` with enterprise news monitoring

Using `time_range: "week"` combined with `search_depth: "advanced"` causes:
- 80%+ irrelevant results (SEO spam, unrelated domains, job postings)
- Cross-company name collisions (e.g. "富海" matches "冬海集团" financial reports)
- Spam/adult content infiltration

**Always use `search_depth: "basic"` without `time_range`** for best relevance on enterprise names.

### 2. `include_raw_content` is almost never useful

Raw content is full of HTML tags, navigation menus, footer text, and CSS class names. The `content` field is already AI-summarized and much cleaner. If you need more detail, request a separate query with a narrower question.

### 3. Windows Python SSL issue

On Windows with Python 3.13, `urllib.request` and `requests` fail with exit code 49 due to SSL certificate issues. Always use `subprocess.run(["curl", ...])` for Tavily API calls on Windows.

### 4. Enterprise name disambiguation

Common or short enterprise names (especially Chinese) frequently collide with unrelated entities:
- "某石化企业" ↔ "鸿海科技/冬海集团/新海"
- "某能源集团" ↔ "福能股份" (different company, similar ticker)

Mitigation: check that the company name (or its first 2 chars) appears in the title or content before accepting a result. Use score threshold + keyword filter. **For problematic names, alias the search term**: e.g. use "富海控股" instead of "某石化企业" to avoid matching 鸿海科技/冬海集团.

### 5. Date extraction from content

Tavily does NOT return a structured `published_date` field. Dates appear inside the `content` text in formats like:
- `2026年6月4日`
- `6月4日`
- `2026-06-04`
- `06/04/2026`

Use regex to extract from content[:300], then attach to each output item.
