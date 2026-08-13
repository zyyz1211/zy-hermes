---
name: think-office-review-pipeline
description: "多角色自动化流水线：think 出方案 → office 执行 → review 审核 → 用户决策。用户的三角色协作流程。"
version: 1.0.0
author: 用户
tags: [pipeline, multi-agent, workflow, think, office, review, 自动化]
---

# Think → Office → Review 流水线

用户的自动化多角色工作流。一条指令完成"出方案→执行→审核"全流程。

## 触发条件

当用户提到以下关键词时，加载本 skill 并执行流程：
- "跑一下think-office-review流程"
- "自动触发" / "自动化流程"
- "多角色" / "流水线" / "pipeline"
- "think office review"
- 任何要求"出方案→执行→审核"全自动完成的请求

## 执行步骤

### Step 1: think — 出方案
用 `delegate_task` 启动一个 think 角色子 agent，goal 设置为：
```
作为创意规划师，请为以下任务提供2-3个方案，每个方案写明重点事项和预估用时，标注最推荐的方案及理由，给出按天分配的时间建议表。
```
context 中包含用户的基本背景信息（详见 memory 中的用户档案）。

### Step 2: office — 执行落地
取 think 的输出结果，作为 context 传给 office 子 agent：
```
作为办公助理，请按照以下方案执行落地，产出实际文件（Excel、Word、Markdown 等）。不要追问，直接做。
```
goal 设置为具体的执行指令（生成周报、整理文件等）。

### Step 3: review — 审核把关
取 office 的输出结果和文件路径，传给 review 子 agent：
```
作为审核员，请按以下清单检查：
- 🔴 严重：信息是否准确？有无事实错误？
- 🟡 一般：逻辑是否通顺？表达是否清晰？
- 🟢 建议：格式是否规范？有无遗漏？
给出总体评价（通过/修改后通过/不通过）和具体修改建议。
```

### Step 4: 汇总给用户
将三个阶段的结果汇总呈现给用户，让他做最终决策。

## 工作背景（用户）

- 单位：某工程集团经营管理部
- 职责：客户档案管理、战略合作、周报述职、部门工作协调
- 桌面目录结构：
  - `01_客户管理` — 客户档案、商机表
  - `02_战略合作` — 战略协议、高层互动
  - `03_部门工作` — 日常部门事务
  - `04_汇报材料` — 经营例会等汇报PPT
  - `05_周报述职` — 个人周报Excel
  - `06_专项工作` — 专项任务文件
- 周报路径：`C:\Users\<user>\Desktop\05_周报述职\个人周报\`
- 周报文件名格式：`周滚动计划_第{N}周.xlsx`
- 周报模板：A1=标题，A3=姓名+第N周+日期，A4~A10=本周总结，A11=下周重点，A12~A16=周一到周五计划

### ⚡ Token 消耗（重要！）

实测一轮完整 pipeline 的 token 消耗量级（单次任务）：

| 阶段 | 输入 tokens | 工具调用数 | 参考耗时 |
|------|:-----------:|:----------:|:--------:|
| think | ~175K | ~7 | ~50s |
| office | **~2.7M** | ~50 | ~4min |
| review | **~1.2M** | ~35 | ~4min |
| **合计** | **~4M+** | **~90+** | **~10min** |

> office 阶段最烧 token，因为它要反复读文件、试路径、生成文件。review 次之。

**省 token 建议：**
- 只跑 think 阶段，让用户看方案后直接决策（最快最省）
- 小任务（如改几个字、查个信息）直接用当前对话，不要走 pipeline
- 大任务（如写周报、做方案、整档案）才启动完整 pipeline
- office 的 context 不要带 think 的完整输出，精简到核心方案内容即可
- review 的 context 只传文件路径和关键输出，不要传整段内容

### 已知坑

- **日期不可靠**：不要依赖自身记忆中的日期。子 agent 的 context 中必须传入 `date '+%Y-%m-%d %A'` 获取的真实系统日期，否则周报的周数和日期区间会出错。
- **Windows 文件路径**：delegate_task 跑在 WSL 侧时，`write_file` 写 `C:\\` 路径可能不可见。优先用 `execute_code`（Windows Python）创建文件，或在 context 中指定 Windows 原生路径。WSL 终端默认 workdir `C:\Users\<user>` 会导致 `cd` 失败（路径不存在），需要显式设 `workdir="/mnt/c/Users/<user>"`。
- **openpyxl 在 WSL Python 中不存在**，需要用 Windows Python（`C:\Users\<user>\AppData\Local\Programs\Python\Python313\python.exe`）或通过 `execute_code` 执行 Excel 操作。
- **delegate_task 非持久化**：如果父 agent 被中断，子 agent 全部丢失。需要持久化的任务请用 cronjob 或 kanban。
- **context 必须自包含**：子 agent 没有父 agent 的 memory/会话历史，需要把所有背景信息（用户的工作单位、职责、文件路径等）显式传入 context。
- **审核结果中如果有🔴严重问题**，建议让 office 修正后再审一轮。
- **最终决策权在用户**，不要替他决定。
