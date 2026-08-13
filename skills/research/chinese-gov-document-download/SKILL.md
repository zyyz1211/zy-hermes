---
name: chinese-gov-document-download
title: 中国政府规划/政策文件批量下载与格式转换
description: 从政府官网查找、下载、提取并转换中国省级/国家级规划纲要（如十五五规划）为PDF。当直接PDF下载不可用时，主动提取网页正文并转换为格式化的PDF文档。
category: research
triggers:
  - 用户要求下载多个省份的规划文件
  - 用户要求获取中国政府发布的政策/规划文档
  - 需要从政府网页提取正文并转为PDF
  - 批量下载政府文件时遇到防盗链/验证码
---

# 中国政府规划/政策文件批量下载与格式转换

## 通用工作流

### 第1步：查找文件来源
1. 优先搜索 `省政府名.gov.cn` 上的官方发布页面
2. 搜索词格式：`XX省国民经济和社会发展第十五个五年规划纲要 PDF 下载`
3. 搜索词格式：`XX省人民政府 印发 十五五 规划纲要 通知`
4. 检查搜索结果中的 `.gov.cn` 域名，优先于第三方网站

### 第2步：下载直接PDF
- 使用 `curl -L -o 文件名 -# --max-time 60` 下载
- 对政府网站可能需要加 `-e <referer_url>` (Referer头)
- 检查下载结果：`file 文件名` 确认是PDF/DOC而非HTML
- 如果收到HTML（验证码页面、重定向页面），尝试其他来源

### 第3步：从页面提取PDF/DOC附件
- 使用 `web_extract(url)` 获取页面内容
- 查找 `附件：` 或 `.pdf` `.doc` `.docx` 链接
- 注意相对路径需要拼接完整URL

### 第4步：HTML内容→PDF转换（当无PDF附件时）
**不要只报告"无法下载"，主动提取正文并转PDF！**

1. 用 `web_extract(url, char_limit=50000)` 提取页面正文
2. 保存原始内容到文本文件
3. 运行 `text_to_pdf.py` 脚本生成格式化的PDF

## 工具脚本

### text_to_pdf.py
功能: 从原始HTML/文本内容生成格式化PDF

```bash
python text_to_pdf.py "省份名" "原始内容文件.txt"
```

流程:
1. 创建格式化的DOCX（含标题、章节标题、正文样式）
2. 通过LibreOffice headless转换为PDF
3. 自动删除临时DOCX

### LibreOffice路径（Windows）
```
C:\Program Files\LibreOffice\program\soffice.exe
```
转换命令（使用subprocess避免路径引号问题）:
```python
import subprocess
cmd = [libreoffice_path, "--headless", "--convert-to", "pdf", docx_path, "--outdir", output_dir]
subprocess.run(cmd, capture_output=True, text=True)
```

## 常见陷阱

### 1. 验证码拦截
- 教育机构镜像（如fzghc.sdjtu.edu.cn）常有验证码
- 解决方案：换用政府官网直链或其他来源

### 2. 文件路径404
- 部分政府网站的DOC/DOCX附件返回404
- 解决方案：尝试从其他镜像下载

### 3. 合并单元格问题
- 政府表格模板中有大量垂直/水平合并单元格
- 用python-docx写入合并单元格时，数据可能溢出到相邻单元格
- **解决方案**：用XML直接操作 `cell._tc` 替换内容

### 4. 政府网站下载限制
- 需要Referer头的页面：`curl -e <page_url> <file_url>`
- 动态加载内容：考虑使用浏览器工具

### 5. 文件格式检查
下载后务必检查:
```bash
file 文件名
```
期望输出: `PDF document` 或 `Composite Document File V2 Document` (DOC)

如果输出: `HTML document` — 下载失败

## 政府网站PDF来源优先级

1. **省政府官网** `xxx.gov.cn` — 最权威
2. **省发改委网站** — 常为规划发布源头
3. **SSE披露版** `static.sse.com.cn` — 债券公告中含完整规划PDF
4. **tzxm.gov.cn** — 投资项目在线审批平台
5. **高校镜像** — 大学发展规划处转发（需注意验证码）
6. **知政策** `zhizhengce.com` — 政策聚合平台

## 批量下载模式

### 子代理并行搜索
使用 `delegate_task` 分配多个搜索任务并行执行：
- 搜索代理：查找所有省份的PDF链接
- 提取代理：从页面提取附件链接
- 下载代理：批量下载已确认的PDF
