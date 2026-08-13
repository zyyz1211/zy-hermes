---
name: company-ppt-template
description: Build PPTX matching 集团公司 template style.
version: 0.2.0
author: Hermes
platforms: [windows]
metadata:
  hermes:
    tags: [PowerPoint, Template, Presentation, python-pptx]
---

# 集团模板风格PPT制作

使用公司固定模板（`集团公司模板.ppt`）的视觉风格，通过 `python-pptx` 快速生成符合规范的精美 PowerPoint 演示文稿。自动处理标题栏、正文字体、配色和布局，无需手动调整。

**不做什么：** 不修改原始 `.ppt` 模板文件（旧版二进制格式，`python-pptx` 无法读取）；不做图表/动画/复杂形状的逐像素复现——只匹配字体、颜色、尺寸等核心视觉特征。

**依赖：** `python-pptx`（已安装 1.0.2）。

## 何时使用

- 用户要求"用公司模板做一份PPT"
- 需要制作符合某工程集团集团风格的汇报材料
- 需要快速从 markdown 或 JSON 生成批量幻灯片
- 需要从原始文档（.docx、报告文本、分析文章）提取内容并生成PPT
- 需要保持一致的字体（微软雅黑/黑体/Franklin Gothic Medium）和配色

## 前置条件

- `python-pptx` 已安装（`pip install python-pptx`）
- 模板参考文件：`C:\Users\<user>\Desktop\04_汇报材料\集团公司模板.ppt`
- 脚本路径：`~/.hermes/skills/productivity/company-ppt-template/scripts/create_ppt.py`

## 如何运行

通过 `terminal` 工具调用辅助脚本 `create_ppt.py`，支持三种输入方式：

1. **Markdown 文件/字符串** — 用 `---` 分页，`#` 标题，`-` 列表项
2. **JSON 文件** — 结构化的幻灯片定义数组
3. **命令行参数** — 快速单页（仅封面）

## 快速参考

```bash
# 从 markdown 文件生成
python scripts/create_ppt.py -o output.pptx --markdown content.md

# 从 JSON 文件生成
python scripts/create_ppt.py -o output.pptx --slides slides.json

# 从命令行快速生成封面
python scripts/create_ppt.py -o output.pptx --title "汇报标题" --subtitle "汇报人：张三  2025年7月"
```

## 操作步骤

### 1. 准备内容

推荐用 markdown 编写幻灯片内容，每条 `---` 分隔一张幻灯片：

**content.md：**
```markdown
# 某工程集团
## 2025年上半年经营工作汇报
---
## 一、主要指标完成情况
- 新签合同额 XXX 亿元，完成年度计划 XX%
- 营业收入 XXX 亿元，同比增长 XX%
- 利润总额 XX 亿元，同比增长 XX%
---
## 二、存在的主要问题
- 部分企业完成目标难度较大，缺口约 XX 亿元
- 项目结算推进缓慢，完工未结算金额 XX 亿元
---
## 三、下一步工作举措
- 全力以赴确保年度指标超额完成
- 聚焦主责主业守好基本盘
- 深化实施"T+EPC"模式
```

### 2. 生成 PPTX

通过 `terminal` 工具执行：

```bash
python "C:\Users\<user>\.hermes\skills\productivity\company-ppt-template\scripts\create_ppt.py" \
  --output "/c/Users/<user>/Desktop/汇报材料.pptx" \
  --markdown "/c/Users/<user>/Desktop/content.md"
```

### 3. 精细调整

如果需要更精确的逐页控制，使用 JSON 格式：

```json
[
  {"layout": "title", "title": "主标题", "subtitle": "副标题"},
  {"layout": "content", "title": "一、章节标题", "subtitle": "（一）子标题", "body": ["要点1", "要点2"]},
  {"layout": "section", "title": "章节分隔页", "body": ["子项1", "子项2"]},
  {"layout": "end"}
]
```

脚本自动在末尾添加"汇报结束，谢谢！"结束页（可通过 `--end-slide False` 禁用）。

## 从文档生成PPT（多Agent并行模式）

当输入是原始文档（如 .docx 分析报告、长篇文本）而非预结构化内容时，使用并行子Agent模式：

### 工作流程

```
┌─────────────────┐     ┌─────────────────┐
│  Agent 1: 内容拆解 │     │  Agent 2: 视觉设计 │
│  ─────────────── │     │  ─────────────── │
│  读取完整文档       │     │  确认模板配色方案    │
│  提取关键信息       │     │  建议布局类型       │
│  生成JSON幻灯片定义  │     │  建议数据展示形式    │
│  输出: slides.json │     │  输出: 设计规范JSON  │
└────────┬────────┘     └────────┬────────┘
         └──────────┬────────────┘
                    ▼
         ┌─────────────────────┐
         │  主Agent: 生成PPT    │
         │  ───────────────── │
         │  合并内容+设计输入    │
         │  调用create_ppt.py   │
         │  输出: output.pptx   │
         └─────────┬───────────┘
                   ▼
         ┌─────────────────────┐
         │  Agent 3: 审核      │
         │  ───────────────── │
         │  视觉QA检查         │
         │  内容完整性检查      │
         │  输出: 审核报告      │
         └─────────────────────┘
```

### 第1步：内容拆解Agent（delegate_task）

将文档全文传给子Agent，要求生成JSON幻灯片定义数组：

```json
// slides.json 格式（每项一个幻灯片）
[
  {
    "layout": "title",
    "title": "报告主标题",
    "subtitle": "副标题/日期"
  },
  {
    "layout": "content",
    "title": "一、章节标题",
    "subtitle": "（一）子标题（可选）",
    "body": [
      "核心要点1（带关键数字）",
      "核心要点2",
      "  缩进子要点（以2空格开头自动降级为二级）"
    ],
    "note": "演讲备注（可选）"
  },
  {
    "layout": "section",
    "title": "章节分隔页",
    "body": ["子项1", "子项2"]
  },
  {
    "layout": "end"
  }
]
```

**内容拆解要点：**
- 控制在12-15页（含封面和结束页）
- 每页3-5个要点，突出关键数字
- 数据密集内容合并，不要逐条罗列
- 结论页放最后，突出核心判断
- 使用 `delegate_task` 的 `goal` + `context` 传参，role='leaf'

### 第2步：视觉设计Agent（并行）

同时启动设计子Agent，返回设计规范：

```json
{
  "palette": {
    "primary": "#002060",
    "secondary": "#0070C0",
    "accent": "#00B0F0",
    "body": "#333333",
    "red_accent": "#FF0000"
  },
  "typography": {
    "title_font": "Franklin Gothic Medium",
    "body_font": "微软雅黑",
    "title_size": "36pt Bold",
    "body_size": "14pt"
  },
  "layout_guidance": {
    "data_comparison": "大数字callout + 左右对比布局",
    "regional_distribution": "信息卡片 + 图标组合",
    "timeline": "横向流程箭头",
    "project_table": "关键字段摘要卡片"
  },
  "special_elements": {
    "footer": "每页底部加入'经营管理部'品牌标识",
    "data_display": "关键数据用大号加粗数字突出"
  }
}
```

**设计要点：**
- 确认使用集团模板配色（深藏青#002060标题栏 + 白色文字）
- 数据展示页使用大数字callout、对比柱状、信息卡片
- 每页底部加品牌标识或页脚
- 报告中涉及某工程集团参建项目的，在页脚或备注中标注

### 第3步：生成PPTX

合并内容JSON，调用 create_ppt.py：

```bash
# 先将内容JSON写入临时文件
cat > /tmp/slides.json << 'JSONEOF'
[{"layout":"title","title":"...","subtitle":"..."}, ...]
JSONEOF

# 生成PPTX
python "/c/Users/<user>/.hermes/skills/productivity/company-ppt-template/scripts/create_ppt.py" \
  --output "/c/Users/<user>/Desktop/输出文件.pptx" \
  --slides /tmp/slides.json
```

### 第4步：审核Agent

启动审核子Agent检查：
- 内容完整性（是否遗漏关键章节）
- 数据准确性（数字是否与原文一致）
- 视觉效果（布局是否合理）
- 使用集团模板风格一致性

### 注意事项

- 子Agent之间是并行关系，使用 `delegate_task` 的 `tasks` 数组同时启动
- 内容拆解Agent和设计Agent无依赖关系，可同时运行
- 审核Agent依赖PPTX生成结果，需在主Agent生成完成后启动
- 最终决策权在用户（用户），审核报告返回后由用户拍板

## 模板风格参考

从实际成品 PPTX 中提取的视觉规范：

| 元素 | 规格 |
|------|------|
| 幻灯片尺寸 | 13.33" × 7.50"（宽屏 16:9） |
| 标题栏字体 | 微软雅黑 24pt Bold，白色（同时设置 Latin + East Asian 字体） |
| 标题栏背景色 | #2A519E（实测从实际成品提取，比#002060稍亮，白底上更有层次感） |
| 小节标题字体 | 微软雅黑 18pt Bold，#002060 |
| 正文字体 | 微软雅黑 14pt，#333333 |
| 封面/结束页背景 | #002060 |
| 封面标题 | Franklin Gothic Medium 36pt Bold，白色 |
| 装饰元素字体 | Franklin Gothic Medium |
| 数字/英文 | Franklin Gothic Medium / Arial |
| 强调色 | #0070C0（蓝）、#00B0F0（浅蓝）、#FF0000（红） |

## 常见问题

- **模板是 .ppt 格式无法直接读取**：`python-pptx` 只支持 .pptx。本脚本用 python-pptx 重新创建匹配风格的 PPTX，不依赖原模板文件。如需精确复刻原模板中的形状/背景图，建议先打开原 .ppt 用 PowerPoint 另存为 .pptx，然后通过 `--template` 参数传入。
- **中文显示正常但英文显示错位**：脚本默认标题栏用"微软雅黑"，封面标题用 "Franklin Gothic Medium"（与原模板一致）。如果系统没有这些字体，PowerPoint 会替换为默认字体，但不影响排版。
- **生成的 PPTX 在 PowerPoint 中打开字体不同**：确保系统安装了微软雅黑和 Franklin Gothic Medium。WPS 用户可能需要手动调整。
- **字体渲染为宋体/Calibri 而非微软雅黑**：`python-pptx` 的 `p.font.name` 只设置拉丁（Latin）字体，中文需要额外设置东亚（East Asian）字体 `a:ea`。脚本中 `_set_font()` 函数通过直接操作 XML 的 `pPr/rPr/a:ea` 元素解决了此问题。如果手动用 python-pptx 写代码，必须同时设置 `rPr/a:ea` 的 `typeface` 属性，否则中文回退到宋体。参考 `create_ppt.py` 中的 `_set_font()` 实现。

## 验证方法

在 `terminal` 中运行以下命令验证脚本可用：

```bash
python "C:\Users\<user>\.hermes\skills\productivity\company-ppt-template\scripts\create_ppt.py" \
  --output "/c/Users/<user>/Desktop/测试_模板风格.pptx" \
  --title "测试标题" --subtitle "验证脚本"
```

生成的 PPTX 应包含：封面页（深蓝背景白字）和结束页（"汇报结束，谢谢！"）。
