---
name: think-office-review-pipeline
description: 多角色自动化流水线：think 出方案 → office 执行 → review 审核 → 用户决策。道一的三角色（think/office/review）工作流。
version: 1.0.0
---

# think → office → review 流水线

## 适用场景

当任务需要先思考方案、再执行、再审核时，使用三角色流水线：

1. **think**：出方案、列要点
2. **office**：执行落地
3. **review**：审核检查

最终由用户（道一）决策。

## 说明

这是 Hermes 多 profile 工作流的抽象，实际执行依赖 Hermes profiles（think/office/review）。
