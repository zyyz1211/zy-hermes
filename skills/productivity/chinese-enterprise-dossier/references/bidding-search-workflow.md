# 招投标搜索工作流 (Bidding/Tendering Search Workflow)

搜索中国招标/投标网站获取项目招标公告和中标结果 — 三层 fallback 策略。

## 触发条件

用户询问：招投标情况、中标结果、招标公告、项目招投标、采购信息等。

## 环境约束

中国招标网站有三大障碍：
- **SPA/JS渲染** — Vue.js/Nuxt.js，简单 HTTP GET 返回空壳
- **反爬保护** — 百度、搜狗等重定向到验证码页面
- **WSL DNS间歇性故障** — `wsl --shutdown` (Windows PowerShell) 恢复

## 三层搜索策略

### Layer 1: Bing with site: operator (最可靠)

```python
import urllib.request, ssl, urllib.parse
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
           'Accept-Language': 'zh-CN,zh;q=0.9'}
q = 'site:ggzy.gov.cn OR site:chinabidding.com.cn OR site:chinabidding.cn ' + 关键词
url = 'https://www.bing.com/search?q=' + urllib.parse.quote(q) + '&count=10'
r = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15, context=ctx)
```

**推荐 site: 目标：**
- `site:ggzyfw.fujian.gov.cn` — 福建公共资源交易
- `site:chinabidding.com.cn` — 中国采购与招标网
- `site:chinabidding.cn` — 中国招标投标网
- `site:cebpubservice.com` — 中国招标投标公共服务平台

### Layer 2: 直接 URL 验证

确认搜索到的 URL 可访问，且页面标题与预期一致。

### Layer 3: 直接招标站搜索 (最不可靠)

大部分招标站是 Nuxt.js SPA，搜索功能不可用。但已知详情页 URL 可直接访问。

## 已知站点可访问性 (WSL实测)

| 站点 | HTTP | 搜索? | 备注 |
|------|------|-------|------|
| chinabidding.com.cn | ✅200 | ❌(SPA) | 详情页可用 |
| chinabidding.cn | ✅200 | ❌(SPA) | 同上 |
| bidcenter.com.cn | ✅200 | ❌(反爬) | 反爬重定向 |
| ggzyfw.fujian.gov.cn | ⚠️ | ❌ | 间歇性故障 |
| cebpubservice.com | ⚠️502 | ❌ | 服务端问题 |
| bing.com | ✅200 | ✅ | 最佳搜索引擎 |

## 信息提取

Bing 结果页 HTML 模式：
```python
# Pattern 1: <li class="b_algo">...</li>
results = re.findall(r'<li class="b_algo">(.*?)</li>', html, re.DOTALL)
# Pattern 2: <h2><a href="...">title</a></h2>
links = re.findall(r'<h2><a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a></h2>', html)
```

## 数据完整性

**永不编造招标/投标信息。** 如果搜索无结果，如实说明：
- "未找到招标公告"/"未找到中标结果"
- "来源不可验证"
- 每条结果必须可溯源到已验证 URL

## 陷阱

1. **SPA空壳** — HTTP 200 不代表获取到有用内容，检查响应体是否包含实际数据
2. **DNS超时** — 多站同时失败"Name or service not known"时，先重启WSL
3. **验证码误判** — 200 但跳转到验证码页面不算成功
4. **时效性** — PC总承包招标需30-60天评审，"无结果"属正常

## 实战案例

`references/fujian-fuduobang-2026-05-19.md` 记录了福建某化工企业项目的完整搜索记录。
