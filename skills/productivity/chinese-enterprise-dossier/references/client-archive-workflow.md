# 客户档案工作流 (Client Archive Workflow)

创建某工程集团经营管理部客户档案 .docx 文件的完整流程 — 5大章节 + 4个附表。

## 触发条件

用户要求创建/生成 XX企业/公司 的档案（"档案"、"客户档案"、"客户信息"、"企业调研"等关键词），或要求"按照那个模板"/"参照XX文件的结构"创建。

## 两种驱动模式

- **模板驱动** — 用户未指定参考结构时，使用五大章节+附表模板
- **参考文档驱动** — 用户引用具体文件（如"按某发电集团那个docx的结构"），用 python-docx 提取该文档段落骨架作为结构模板

## 工作流 (5步)

### Step 1: 搜索本地已有资料

搜索桌面、客户管理文件夹等目录中与目标企业相关的现有文件。

```bash
find /mnt/c/Users/<user>/Desktop -iname "*目标企业*" 2>/dev/null
```

支持的格式：.docx / .xlsx / .pdf / .pptx / .txt / .md

⚠️ **记录资料来源日期**（以文件创建/修改时间为准），后续 Step 3 中逐一验证最新状态。

### Step 2: 获取模板结构

读取现有客户档案 .docx 作为模板：
```python
import docx
doc = docx.Document('/mnt/c/.../档案.docx')
for p in doc.paragraphs:
    if p.text.strip(): print(f'[{i}] {p.text}')
```

模板骨架详见 `references/template-structure.md`。

### Step 3: 调研目标企业（含跟踪项目状态验证）

使用 `delegate_task` 并行调研。**调研优先级：**

1. 🎯 **官网优先** — 访问目标企业官网「集团动态」/「新闻中心」版块
   - SSL 绕过：`ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE`
   - HTTPS 失败时回退到 HTTP
   - 详见 `references/chinese-web-search.md` 和 `references/company-website-research-case.md`
2. **百度百科**、行业新闻网站
3. **招标网站**（如 chinabidding.com.cn）
4. **搜索引擎**（补充手段，可能空结果）

**调研信息需求：** 公司全称/法定代表人/总部/企业类型/经营范围/核心竞争力/管理层/对接部门/短期规划/中长期战略/财务状况/历史合作/风险提示/跟踪项目

**⚠️ 跟踪/历史项目状态验证（关键！）：**
- 对每个本地资料中的"跟踪项目"，搜索其最新状态（开标/中标/签约/完工）
- 确认历史合作项目是否已完工结算、有无新增合同
- 方法：Bing 搜索「项目名称 + 中标/招标/开工/完工 + 关键词」
- 无法验证的项目标注"据XX年XX月资料，建议核实最新状态"

**遇到反爬时：** 加载 `browser-skills` (`skill_view('browser-skills')`) 获取百度专用 CSS 选择器和操作方案。

### Step 4: 生成 .docx 文件

使用 `templates/archive-generator.py` 生成文档。

**格式标准 (GB/T 9704-2012):** 详见 umbrella SKILL.md 的「文档格式标准」章节。

**关键实现细节：**
- 页面布局：A4, 上37/下35/左28/右26mm
- 各层级字体字号（黑体标题、楷体节标题、仿宋正文、宋体表格）
- 固定行距28磅 + 首行缩进2字符
- 表格使用 'Table Grid' 样式

**输出路径：**
```
C:\Users\<user>\Desktop\客户管理工作\客户档案\{企业简称}集团档案.docx
WSL: /mnt/c/Users/<user>/Desktop/客户管理工作/客户档案/{企业简称}集团档案.docx
```

### Step 5 (推荐): 并行校对检查

派出独立校对 Agent 检查：内容准确性 / 结构完整性 / 公文格式合规 / 语言专业性 / 视角一致性 / 漏项检查。

⚠️ **校对 Agent 无法直接读取 .docx**。需用终端提取全文传给 Agent，或在生成脚本末尾 print 所有段落文本。

## 已有文档格式重排

用户已有写好的 .docx 需调整排版格式时，使用 `scripts/reformat-existing-archive.py`。该脚本自动识别每个段落的层级并重新设定字体字号行距缩进。

## 已知陷阱

1. **文件编码** — `write_file` 可能写入 UTF-16 BOM。写入后 `file <path>` 检查。优先用 heredoc 写脚本
2. **中文引号** — heredoc 中的中文引号（""）会被转为 ASCII 引号，用 `\u201c` / `\u201d` 转义
3. **文件锁定** — Word 打开文件时无法覆盖，加 `_v{YYYYMMDD}` 后缀另存
4. **非上市企业财务** — 标注"未公开披露"，使用"据行业研报估算"前缀
5. **勾选框格式** — `☑` 表示选中，`□` 表示未选中
