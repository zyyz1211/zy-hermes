---
name: chinese-enterprise-dossier
description: "中国化工企业档案与报告 — 调研中国企业，生成格式化 .docx 文档（客户档案、政策研究报告、招投标搜索）。适用某工程集团经营管理部。"
tags:
  - enterprise-research
  - document-generation
  - docx
  - chinese-government
  - bidding
  - policy-analysis
  - china-chemical-engineering
---

# Chinese Enterprise Dossier (中国化工企业档案与报告)

## 适用范围

本技能涵盖为某工程集团经营管理部进行的以下三类文档工作：

| 文档类型 | 原始技能 | 详见 |
|---------|---------|------|
| **A. 客户档案** | `productivity/client-archive` | `references/client-archive-workflow.md` |
| **B. 政策研究报告** | `productivity/policy-research-report` | `references/policy-report-workflow.md` |
| **C. 招投标搜索** | `research/chinese-bidding-search` | `references/bidding-search-workflow.md` |
| **D. 二级企业“十五五”规划审核** | 集团总部经营审核意见 | `references/fifteen-five-plan-review.md` |
| **E. 内部知识库主题挖掘** | 从领导讲话/内部PDF集合中提取专题内容，跨文档对比分析，用于完善汇报材料 | `references/internal-knowledge-mining.md` |
| **F. 客户项目进展报告** | 更新已有项目初稿，基于公开信息查询补充最新进展、技术细节、竞争格局、风险评估及跟踪建议，输出格式化 .docx 呈报领导 | `references/project-progress-report-workflow.md` |

## 共享基础设施

### 环境约束 (WSL + Windows)

| 约束 | 说明 |
|------|------|
| Python-docx 路径 | `~/.local/open-webui-venv/bin/python3.11` (venv Python 3.11) |
| 文件编码陷阱 | `write_file` 可能写入 UTF-16 BOM。写入后立即 `file <path>` 验证。优先用 heredoc 写脚本 |
| DNS 失步 | WSL DNS 间歇性故障。恢复: Windows PowerShell → `wsl --shutdown`，然后重新进入 |
| SSL 证书 | 中文网站常有证书问题: `ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE` |
| 文件锁定 | Word 打开 .docx 时无法覆盖。加 `_v{YYYYMMDD}` 后缀另存 |

### 企业调研方法论

所有三类文档共享相同的信息采集技术：

**优先级：**
1. 🎯 **官网优先** — 直接访问目标企业「新闻中心」/「集团动态」版块，SSL 绕过模板
2. **次选** — Bing 搜索（`site:` 操作符限定域名），百度搜索（无 JS 时可能触发 CAPTCHA）
3. **第三** — 招标网站（中国采购与招标网等）
4. **最后** — 搜索引擎补充

**技术模板：**
```python
import urllib.request, ssl, urllib.parse
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
           'Accept-Language': 'zh-CN,zh;q=0.9'}
```

**WSL 网络诊断（先于任何 fallback）：**
```python
hosts = ['www.baidu.com', 'www.bing.com', 'www.chinabidding.com.cn']
for h in hosts:
    try:
        ip = socket.getaddrinfo(h, 80)[0][4][0]
        req = urllib.request.Request(f'https://{h}', headers=headers)
        r = urllib.request.urlopen(req, timeout=10, context=ctx)
        print(f'{h}: DNS={ip}, HTTP={r.status}')
    except Exception as e:
        print(f'{h}: {type(e).__name__}: {str(e)[:60]}')
```

区分 DNS 故障（`Name or service not known` → 重启 WSL）vs 反爬（403/CAPTCHA → 加载 browser-skills）。

### 文档格式标准 (GB/T 9704-2012)

| 层级 | 元素 | 字体 | 字号 | 其他 |
|------|------|------|------|------|
| 标题 | 文档标题 | 黑体 | 二号(22pt) | 居中 |
| H1 | `一、二、三...` | 黑体 | 三号(16pt) | 加粗，首行缩进2字符 |
| H2 | `（一）（二）...` | 楷体_GB2312 | 三号(16pt) | 首行缩进2字符 |
| H3 | `1. 2. 3. ...` | 仿宋_GB2312 加粗 | 三号(16pt) | 首行缩进2字符 |
| 正文 | 普通段落 | 仿宋_GB2312 | 三号(16pt) | 首行缩进2字符，固定行距28磅 |
| 基本信息行 | `客户全称：...` | 仿宋_GB2312 | 三号(16pt) | 不计缩进，加粗标签 |
| 表格 | 表格内容 | 宋体 | 五号(10.5pt) | 表头加粗居中，全边框 |

页面: A4, 上37mm/下35mm/左28mm/右26mm。

### 关键原则

1. **每条数据必须可溯源** — 子公司名称、合同额、项目进度来自公开信息或用户确认
2. **不编造** — 搜索不到时标注"据公开信息暂无"或"未公开披露"
3. **定量优于定性** — "省税约500万元"比"降低税负"更有说服力
4. **用户是信息源** — 内部架构信息（如"南投国贸→南方建设投资"），主动询问
5. **校对检查** — 生成后派出独立校对 Agent（通过终端提取 .docx 全文传给 Agent）

---

## A. 客户档案工作流

详见 `references/client-archive-workflow.md`。

**快速启动：**
1. 搜索本地已有资料（桌面、客户管理文件夹）
2. 读取模板结构（现有客户档案 .docx 或 `references/template-structure.md`）
3. 调研目标企业（官网优先，`delegate_task` 并行）
4. ⚠️ **跟踪/历史项目状态验证** — 每个项目联网搜索确认最新进展，不能照搬旧资料
5. 生成 .docx（`templates/archive-generator.py`），保存到 `客户管理工作/客户档案/`
6. 可选：校对 Agent 检查

**两种驱动模式：**
- **模板驱动** — 使用正式五大章节+附表模板
- **参考文档驱动** — 用户引用具体文件（如"按某发电集团那个docx的结构"），提取该文档的段落骨架

**已写好的文档重排：** 使用 `scripts/reformat-existing-archive.py` 进行 GB/T 9704-2012 格式重排。

---

## B. 政策研究报告工作流

详见 `references/policy-report-workflow.md`。

**快速启动：**
1. 读取原始报告（python-docx 提取段落和表格）
2. 搜索集团在相关领域的实际布局（子公司、项目、业绩）
3. 建立信息映射关系：泛化表述 → 具体实体（含量化）
4. 新增"结论与建议"章节（6-8条可执行建议，含操作主体+量化目标+时间节点）
5. 生成公文格式 .docx（`templates/report-generator.py`）

**关键区别 vs 客户档案：** 政策报告更强调战略视角（"纳入十五五规划"）、定量化建议、已知集团实体列表（见 `references/hainan-layout.md`）。

---

## C. 招投标搜索工作流

详见 `references/bidding-search-workflow.md`。

**三层策略（按优先级）：**
1. **Bing `site:` 操作符** — 最可靠。`site:ggzy.gov.cn OR site:chinabidding.com.cn <关键词>`
2. **直接 URL 验证** — 确认搜索结果的目标页面可访问
3. **直接招标站搜索** — 大多为 SPA，搜索功能不可用，但已知详情页可直访

---

## D. 二级企业“十五五”规划审核

详见 `references/fifteen-five-plan-review.md`。

**核心口径：** 以集团总部审核人员身份直接提出判断，不要在意见中写“经营管理部关注……”等自我说明式表述。输出通常按“行文内容方面 / 量化数据方面”各 1–2 条，要求简洁、具体、可修改、可核验。

---

## 支持文件

| 目录 | 文件 | 来源 |
|------|------|------|
| `references/` | `client-archive-workflow.md` — 客户档案完整流程 | absorbed from client-archive SKILL.md |
| `references/` | `policy-report-workflow.md` — 政策报告完整流程 | absorbed from policy-research-report SKILL.md |
| `references/` | `bidding-search-workflow.md` — 招投标搜索完整流程 | absorbed from chinese-bidding-search SKILL.md |
| `references/` | `chinese-web-search.md` — 中文网站搜索策略 | from client-archive |
| `references/` | `company-website-research-case.md` — 某能源集团集团调研案例 | from client-archive |
| `references/` | `template-structure.md` — 五大章节+附表模板 | from client-archive |
| `references/` | `hainan-layout.md` — 已知在琼实体列表 | from policy-research-report |
| `references/` | `fujian-fuduobang-2026-05-19.md` — 招投标实战案例 | from chinese-bidding-search |
| `references/` | `fifteen-five-plan-review.md` — 二级企业“十五五”规划审核意见写法 | from session learning |
| `references/` | `internal-knowledge-mining.md` — 内部PDF知识库主题挖掘完整工作流 | from session learning (集团领导讲话"海外"主题实战) |
| `references/` | `project-progress-report-workflow.md` — 客户项目进展报告更新工作流 | from session learning (富海曹妃甸项目进展报告实战) |
| `templates/` | `archive-generator.py` — 客户档案生成脚本 | from client-archive |
| `templates/` | `report-generator.py` — 政策报告生成脚本 | from policy-research-report |
| `templates/` | `docx-reformat.py` — docx 格式重排模板 | from client-archive |
| `scripts/` | `reformat-existing-archive.py` — 已有文档重排 | from client-archive |
| `templates/` | **`gongwen-docx-builder.py`** — 公文格式Word文档构建器（可复用模块） | from session learning |

## 公文格式文档快速生成

使用 `templates/gongwen-docx-builder.py` 中的 `GongwenDocxBuilder` 类，可快速将结构化内容（MD、研究笔记等）转换为公文格式 .docx：

```python
from templates.gongwen_docx_builder import GongwenDocxBuilder

builder = GongwenDocxBuilder()
builder.add_title('调研报告标题')
builder.add_h1('一、基本情况')
builder.add_body('正文内容……')
builder.add_table(['序号','项目名称','状态'], [['1','示例','在建']])
builder.save('输出路径.docx')
```

可用方法：
- `add_title(text)` — 黑体22pt居中标题
- `add_h1(text)` / `add_h2(text)` — 一级/二级标题
- `add_body(text)` — 仿宋正文
- `add_body_bold_prefix(prefix, text)` — 标注性文字（如"解读："）
- `add_quote(text)` / `add_note(text)` — 引文/注释
- `add_table(headers, data)` — 表格
- `add_blank()` — 空行
- `save(path)` — 保存
