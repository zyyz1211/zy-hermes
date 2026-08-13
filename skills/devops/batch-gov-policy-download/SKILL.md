---
name: batch-gov-policy-download
description: 批量下载中国政府/省级政策文件（PDF/DOC/DOCX），从政府官网定位、提取附件链接并下载
trigger: 用户要求下载多个省份/部委的政策文件（如"十五五"规划、专项规划等）
---

# 中国政府政策文件批量下载

适用于需要从中国政府网站批量下载政策文件（如各省"十五五"规划纲要、部委专项规划等）的场景。

## 工作流

### 第一步：收集链接源

优先从汇总文章获取链接列表，其次是逐个搜索：

1. **汇总文章**：微信公众号、行业报告网站等常发布含31省链接的汇总文章
   - 用 `web_extract` 提取文章内容
   - 提取所有省份的微信文章链接或政府官网链接
   - ⚠️ 微信文章本身无法直接通过 curl 下载，需提取其中的政府官网链接

2. **逐个搜索**：对每个省份搜索 `XX省/市国民经济和社会发展第十五个五年规划纲要 PDF 下载`
   - 使用 `web_search` 搜索
   - 优先筛选 `.gov.cn` 域名结果
   - 优先找PDF直链，其次是发布页面

### 第二步：并行搜索（使用 delegate_task）

```python
# 适合批量搜索的场景：派发一个子代理搜索31个省份
delegate_task(
    goal="搜索31个省份的'十五五'规划纲要PDF下载链接",
    context="返回JSON数组 [{province, url, status}]"
)
```

子代理返回结果后用 JSON 文件保存，后续读取使用。

### 第三步：提取PDF直链

从政府发布页面提取附件下载链接：

1. **直接PDF链接**（最理想）：`xxx.pdf` 结尾的URL，直接 `curl -L -o filename.pdf "url"`
2. **政府页面附件链接**：提取页面中类似 `href="33952633/files/xxx.docx"` 的相对路径
   - 需要拼接 base URL 构造完整下载链接
   - 有些需要加 Referer header: `curl -e "referer_url" -o file "download_url"`
3. **验证码页面**：如山东交通学院等教育网站，需要输入验证码才能下载——跳过
4. **内容页**：部分省份只有HTML页面（如四川、湖北），没有可下载的PDF附件

### 第四步：批量下载

```bash
cd "/path/to/download/dir"
# 直接PDF
curl -L -o "省份名十五五规划纲要.pdf" "pdf_url" -# --max-time 60
# 需要Referer的
curl -L -o "省份名十五五规划纲要.docx" -e "页面URL" "附件URL" -# --max-time 60
# 验证文件类型
file "省份名十五五规划纲要.pdf"
```

## 常见模式

### 省级规划发布页面URL模式

| 类型 | 示例 |
|------|------|
| 省级政府门户 | `https://www.XX.gov.cn/.../t2026...html` |
| 发改委网站 | `https://drc.XX.gov.cn/.../content_...html` |
| 第三方转载 | `https://www.zhizhengce.com/policies/...` |
| 高校转载 | `https://fzghc.XX.edu.cn/info/.../...htm` |

### 附件链接提取示例

```
湖南: 页面路径/33952633/files/b2a09017b458429591bd645cadb51c53.docx
黑龙江: 页面路径/31926227/files/黑政发4号.doc
吉林: xxgk.jl.gov.cn/PDFfile/202604/9478891.pdf
海南: zhizhengce.com/files/attachment/.../...doc
```

### 特殊处理

- **上海/浙江**：部分可通过 `shanghaiinvest.com/cn/viewfile.php?id=XXXXX` 访问
- **吉林省政府信息公开页**：有 `pdf下载` 和 `word下载` 按钮，链接格式 `//xxgk.jl.gov.cn/PDFfile/202604/9478891.pdf`
- **URL编码**：中文文件名需用 `%` 编码，或直接用 curl 的 `--path-as-is`

## 已知限制

1. 约半数省份（约15-20个）没有提供独立的PDF/DOC下载，仅以HTML网页形式发布
2. 部分网站有反爬机制（验证码、Referer检查、Session验证）
3. 政府网站文件可能被移除（返回404）
4. 微信公众号文章无法直接通过 web_extract 或 curl 抓取

## 文件组织

下载后的文件统一存放在一个目录中，命名格式为：
```
省份名十五五规划纲要.pdf   (如 北京市十五五规划纲要.pdf)
省份名十五五规划纲要.doc   (如 海南省十五五规划纲要.doc)
```

## 验证

下载后用 `file` 命令验证文件类型：
```bash
file "省份名十五五规划纲要.pdf"
# 应输出: PDF document, version X.X
```
