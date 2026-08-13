# 中文网站搜索技术参考

WSL 环境中通过 HTTP 访问中文网站的有效方法。验证日期：2026-05-19。

## 前提：WSL 网络恢复

如果遇到 `Name or service not known` 或 `Network is unreachable`：

```powershell
# Windows PowerShell（无需管理员）
wsl --shutdown
# 然后重新进入 WSL
```

或双击桌面 `C:\Users\<user>\Desktop\fix-wsl-network.ps1`

## 通用请求模板

```python
import urllib.request, ssl, urllib.parse

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

req = urllib.request.Request(url, headers=headers)
r = urllib.request.urlopen(req, timeout=15, context=ctx)
body = r.read(5000)
html = body.decode('utf-8', errors='replace')
```

注意：WSL 的 curl 在处理中文参数时可能有字符问题（bash 循环中变量含中文会出错），建议用 Python urllib。

## ⚠️ 关键技巧：HTTPS → HTTP 回退

**WSL 中访问中国企业官网时，HTTPS 经常因 SSL 证书问题失败，回退到 HTTP 即可。** 这是 WSL 环境下最常遇到的障碍：Python urllib 请求公司官网的 `https://` URL 时报 SSL 错误或连接超时，但同一域名的 `http://` 端口仍正常工作。

**具体做法：** 当 `https://www.{company}.com` 失败时，直接尝试 `http://www.{company}.com`（不带 s）。例如某能源集团集团官网 `https://fjnhjt.com` 在 WSL 中 SSL 握手失败，但 `http://fjnhjt.com` 完全正常，可成功获取"集团动态"和"媒体聚焦"文章。

**自动回退代码模板：**

```python
def try_fetch(url, timeout=15):
    """先用 HTTPS，失败后自动回退到 HTTP."""
    import urllib.request, ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    for scheme in ['https', 'http']:
        actual_url = url.replace('https://', f'{scheme}://').replace('http://', f'{scheme}://')
        try:
            req = urllib.request.Request(actual_url, headers=headers)
            resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
            return resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            print(f'  [{scheme}] {actual_url}: {type(e).__name__}')
            continue
    return None
```

## 搜索引擎的实际可用性（实测 2026-05-19）

**重要发现：中文搜索引擎在 WSL 中基本不可用于自动化搜索。** 所有主流引擎都返回 JavaScript 渲染页面，不含实际搜索结果。

| 站点 | 解析结果 | 实际可用 |
|------|---------|---------|
| `Bing cn.bing.com/search?q=关键词` | HTTP 200，HTML 无搜索结果 | ❌ — JS 渲染，无搜索数据 |
| `Bing RSS format=rss` | HTTP 200，返回无关内容 | ❌ — 中文关键词返回随机结果 |
| `搜狗 sogou.com/web?query=关键词` | HTTP 200，`h3` 标签为空 | ❌ — 反爬/验证码 |
| `百度 baidu.com/s?wd=关键词` | HTTP 200，跳转验证码页面 | ❌ — 反爬验证码 |

**应对策略：不依赖搜索引擎，改为直接访问已知 URL。**

## 可直接访问的资源（已验证）

### 企业信息
| 站点 | 方法 | 实测 |
|------|------|------|
| 公司官网 | 直接访问 `www.{公司域名}.com` | ✅ 可获取领导团队、简介、集团动态新闻等 |
| 公司官网之"集团动态"版块 | 访问 `www.{公司域名}.com/` 后提取新闻列表页链接（如 `/news/`、`/xwzx/`、`/jtdt/`） | ✅ 可直接解析新闻标题和正文 |
| 百度百科 | 直接访问已知词条 URL (https) | ⚠️ 视当前反爬策略而定（有时200有时403，不稳定） |
| 搜狐新闻 `sohu.com` | 直接访问新闻链接 | ✅ |
| 第一财经 `yicaiglobal.com` | 直接访问文章链接 | ✅ |
| 行业新闻 `chemnet.com` | 直接访问文章链接 | ✅ |

### 公司官网新闻版块（已验证的具体案例）

**最可靠的数据来源：目标企业官网的"新闻中心"/"集团动态"版块。** 这些页面通常不是SPA，可直接通过 Python urllib 获取 HTML 并提取新闻列表和正文，获取最新项目进展、高层动态等一手信息。

| 公司 | 官网 | 新闻版块URL模式 | 实测 |
|------|------|----------------|------|
| 某能源集团集团 | `fjnhjt.com` | HTTP:// 直接访问 | ✅ 集团动态 + 媒体聚焦，12条新闻可直接解析 |
| 三钢集团 | `www.fjsg.com.cn` | 首页新闻列表 | ✅ 可访问 |

**工作流程（实测有效）：**
```python
import urllib.request, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

# 步骤1: 访问官网首页，寻找"集团动态""新闻中心"等版块的链接
url = 'http://fjnhjt.com/'  # 注意用 http:// 而非 https://
req = urllib.request.Request(url, headers=headers)
resp = urllib.request.urlopen(req, timeout=15, context=ctx)
html = resp.read().decode('utf-8', errors='replace')

# 步骤2: 从首页提取新闻列表页面的链接（通常包含 /news, /xwzx, /jtdt 等路径）
# 步骤3: 访问新闻列表页，提取各条新闻的标题、日期、链接
# 步骤4: 访问单条新闻页面，提取正文内容
```

### 招标网站
| 站点 | 状态 | 备注 |
|------|------|------|
| `www.chinabidding.com.cn` | ✅ 200 | 首页可访问，搜索是 Nuxt.js SPA 需 JS |
| `www.bidcenter.com.cn` | ✅ 200 | 首页可访问 |
| `www.chinabidding.cn` | ✅ 200 | 首页可访问 |

### 政府交易平台
| 站点 | 状态 | 备注 |
|------|------|------|
| `smggzy.sm.gov.cn`（三明市） | ✅ 200 | SPA 架构，内容需 JS |
| `www.cebpubservice.com` | ⚠️ 502 | 服务端问题 |

## 有效的搜索策略（排序 — 优先级从高到低）

1. **目标企业官网新闻版块** — 访问公司官网查找"集团动态""新闻中心""媒体聚焦"等版块，获取一手项目进展、高层动态。这是最可靠的数据源（无反爬、内容权威、更新及时）。
2. **直接访问已知 URL** — 百度百科词条、公司官网固定页面（如 `about/`、`leadership/`、`news/`）
3. **通过行业新闻网站直接搜索** — 如 `chemnet.com`、搜狐新闻的文章页面
4. **通过 Bing 间接搜索** — 接受可能空结果，作为补充手段
5. **永不依赖搜索引擎的 HTML 解析** — 所有主流搜索引擎都会返回 JS 渲染页面，无法获取结构化搜索结果

## 特殊技术：Bing RSS 格式

```python
url = f'https://cn.bing.com/search?format=rss&q={urllib.parse.quote(keyword)}'
```
此方法返回 XML 格式，可解析 `item/title` 和 `item/link`，但中文关键词返回的结果可能完全不相关（如搜"中沙古雷乙烯"返回"拉蒂兹-龙珠"）。**效果不可靠。**

## 结论

对于某工程集团客户档案调研，当前 WSL 环境无法通过搜索引擎获取特定项目的招投标进展。**必须依赖本地内部资料 + 直接访问已知的公司官网/新闻页面。** 对于搜索引擎无法验证的信息，如实标注"据X年X月资料，建议核实最新状态"。
