---
name: chinese-gov-doc-batch-download
description: 批量从中国政府网站（.gov.cn）下载公文、规划纲要等PDF/DOC文档。涵盖链接提取、多格式附件处理、并行下载。
trigger: 用户要求下载多个省份/部门的政府规划文件、政策原文、白皮书等
---

# 中国政府公文批量下载

适用于批量下载各省/部委的规划纲要、政策文件、白皮书等PDF/DOC文档。

## 工作流程

### 第一步：收集链接

从三种渠道获取文档链接：

**渠道A：聚合文章（微信公众号等）**
```python
# 提取文章中的链接
from hermes_tools import web_extract
result = web_extract(urls=["https://mp.weixin.qq.com/s/..."])
# 文章内的链接通常形如 https://mp.weixin.qq.com/s?__biz=...
```

**渠道B：搜索政府官网**
```python
# 搜索政府网站
from hermes_tools import web_search
result = web_search(query="XX省国民经济和社会发展第十五个五年规划纲要 site:gov.cn")
```

**渠道C：直接访问已知政府页面**
- 省级发改委网站：`fgw.xx.gov.cn`
- 省政府网站：`www.xx.gov.cn`
- 学校/机构转载页（经常有附件）

### 第二步：提取PDF/DOC附件链接

政府页面的附件链接通常有以下几种形式：

**形式1：直接PDF链接**
```
https://xxx.gov.cn/path/file.pdf
```
→ 直接用 curl 下载

**形式2：下载跳转链接（需要验证码）**
```
/system/_content/download.jsp?urltype=news.DownloadAttachUrl&owner=xxx&wbfileid=xxx
```
→ 需要验证码，无法直接下载。尝试搜索其他来源。

**形式3：附件链接在页面中**
```
<a href="files/xxx.pdf">附件下载</a>
```
→ 拼接完整URL：`https://base.gov.cn/current/path/files/xxx.pdf`

**形式4：.doc/.docx 附件**
```
33952633/files/b2a09017b458429591bd645cadb51c53.docx
```
→ 用 curl 下载，注意 URL 拼接

### 第三步：并行搜索 + 批量下载

```python
# 策略：用 delegate_task 派子代理搜索链接
# 同时主代理下载已确认的PDF

# 下载命令
curl -L -o "省份名十五五规划纲要.pdf" "https://..." -# --max-time 60
```

**关于 delegate_task 的使用：**
- 派一个子代理搜索/提取链接，返回JSON数组
- 主代理不等待，直接下载已有链接
- 子代理结果回来后继续下载剩余

### 第四步：处理特殊格式

| 格式 | 处理方式 |
|------|----------|
| `.pdf` | 直接 curl 下载，`-L` 跟随重定向 |
| `.docx` | 可用 LibreOffice 转 PDF 或直接使用 |
| `.doc` | 可用 LibreOffice 转 PDF |

## 常用政府网站模式

### 各省十五五规划纲要常见位置

```
北京: news.bistu.edu.cn/ztwz/swwgh/docs/
天津: www.tjdz.edu.cn/a/institution/scientific_research/files/
辽宁: new.tzxm.gov.cn/zckd/fzgh/
江苏: www.jsdzj.gov.cn/module/download/downfile.jsp
浙江: static.sse.com.cn/disclosure/bond/announcement/local/c/new/
山东: new.tzxm.gov.cn/zckd/fzgh/
西藏: www.xizang.gov.cn/zwgk/xxfb/ghjh/
贵州: szb.eyesnews.cn/pc/att/
```

### 政府页面附件提取规律

- **湖南模式**：附件在 `33952633/files/xxx.docx` 路径
- **黑龙江模式**：附件在 `31926227/files/黑政发4号.doc` 路径
- **山东模式**：学校转发页面有 PDF 附件，但可能需验证码
- **广东模式**：金融办页面 `attachment/0/0/809/42890.pdf`

## 常见陷阱

1. **验证码保护**：学校/机构的下载系统常有验证码，遇此情况跳过或找其他来源
2. **URL编码**：中文文件名需URL编码，`curl` 会自动处理，但路径中有中文时注意
3. **SSL证书**：部分.gov.cn站点证书可能过期，用 `-k` 跳过验证（不推荐生产环境）
4. **大文件超时**：广东等大省PDF可达90MB+，设 `--max-time 120`
5. **合并单元格**：用 python-docx 填写干部履历表等表格模板时，需通过 XML 直接操作 `<w:tc>` 元素，不能用 `cell.text` 写入合并单元格
6. **WeChat文章无法直接抓取**：`web_extract` 对 `mp.weixin.qq.com` 链接会失败，需通过搜索或其他渠道获取内容

## 第五步：网页内容→PDF转换（当无附件可用时）

约半数的省份没有提供PDF/DOC下载，仅以HTML网页形式发布。此时需要提取网页正文→清理→转PDF。

### 流程

1. 用 web_extract 提取网页内容
2. 保存原始内容到 `{province}_raw.txt`
3. 清理文本：去除HTML/markdown表格格式、导航元素
4. 创建格式化DOCX（含标题、章节、来源等）
5. 用 LibreOffice 将DOCX转为PDF
6. 验证输出质量（检查页数和文件大小）

### 内容清理要点

**河北模式（手机版政府页面）**：内容以Markdown表格格式输出，全部挤在一行里。
- 去掉 `|---|` 表格分隔线
- 去掉所有 `|` 竖线
- 将双空格替换为换行
- 去掉链接路径 `(/path)`

**上海模式（政府官网）**：内容较干净，可直接用。

### DOCX→PDF转换

```python
import subprocess
libreoffice = r"C:\Program Files\LibreOffice\program\soffice.exe"
subprocess.run([libreoffice, "--headless", "--convert-to", "pdf", docx_path, "--outdir", output_dir])
# 用 subprocess.run 而非 os.system，避免路径引号问题
```

### 质量验证（必须！）

```bash
file "省份名十五五规划纲要.pdf"
# 应输出: PDF document, version X.X, N page(s)
# 若只有1page或文件极小(数十KB)，说明内容提取失败
```

**重要教训**：河北第一次转换只得到43KB/1页，用户批评"格式都是乱的 真的是瞎胡闹"。修复后重新生成为895KB/76页。必须校验输出质量。

## 验证下载

```bash
# 检查文件大小，排除 HTML 页面伪装
ls -lh *.pdf | awk '{if($5 ~ /^[0-9]+[K]$/) print $NF" 可能不是PDF(太小)"}'
```
