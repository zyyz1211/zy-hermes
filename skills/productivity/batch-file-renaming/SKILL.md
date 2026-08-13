---
name: batch-file-renaming
description: 批量重命名本地文件：按时间顺序、Excel清单序号、企业简称映射等规则添加前缀，并生成可追溯映射日志。
tags: [文件整理, 批量重命名, Excel, openpyxl, Windows, 中文文件名]
version: 1.0.0
---

# Batch File Renaming — 批量文件重命名

## When to use

用户要求整理某个文件夹内文件名，尤其是：

- 按时间顺序添加 `01+文件名`、`02+文件名` 等前缀；
- 参照 Excel 表中的顺序/编号给文件名前添加 `01_`、`02_`；
- 根据企业简称、项目名称、日期、关键词匹配文件；
- 需要避免桌面混乱、脚本可复用、保留重命名记录。

## Core workflow

1. **先列清单**：用 `search_files(target='files')` 或 Python `Path.iterdir()` 获取目标文件夹文件列表。
2. **读取规则来源**：
   - 如果规则来自 Excel，用 Windows Python 或当前可用 Python + `openpyxl` 读取；
   - 如果规则来自文件名时间，优先从文件名解析年份/会议/日期；文件系统 `mtime` 只作为辅助，因为复制文件会改变时间。
3. **生成预览方案**：先输出 `原文件名 -> 新文件名`，检查未匹配文件、重复目标名、已存在前缀。
4. **两阶段重命名**：先统一改成临时名，再改成目标名，避免 A->B、B->A 或同名冲突。
5. **生成映射日志**：在目标文件夹写 `rename_log_YYYYMMDD_HHMMSS.txt`，记录规则来源、原名、新名、匹配依据、未匹配项。
6. **核验结果**：重新列出文件夹，按文件名排序确认前缀顺序正确。

## User preference: script location

用户要求工具类 Python 脚本统一保存到：

- Windows: `C:\Users\<user>\Desktop\09_工具脚本\`
- MSYS/Git Bash: `/c/Users/<user>/Desktop/09_工具脚本/`

不要把脚本直接散放在桌面。

## Implementation pattern

- Python 脚本必须含 `# -*- coding: utf-8 -*-`。
- 读写文本文件显式使用 `encoding='utf-8'`。
- 中文文件名、Windows 路径优先用 raw string：`Path(r"C:\...")`。
- 对已存在序号前缀的文件，先剥离再重新编号，避免 `01_02_文件名`。
- 不确定规则时，不要猜测未匹配文件；保留原名并在日志中列出。

## Skeleton

```python
# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

TARGET_DIR = Path(r"C:\path\to\folder")
PREFIX_RE = re.compile(r"^\d{2}[_+＋＿]")


def strip_existing_prefix(name: str) -> str:
    return PREFIX_RE.sub("", name)


def build_target_name(index: int, name: str) -> str:
    return f"{index:02d}_{strip_existing_prefix(name)}"


def main() -> None:
    files = [p for p in TARGET_DIR.iterdir() if p.is_file()]
    sorted_files = sorted(files, key=lambda p: strip_existing_prefix(p.name))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plan = []
    for idx, src in enumerate(sorted_files, start=1):
        dst = src.with_name(build_target_name(idx, src.name))
        if src != dst:
            plan.append((src, dst))

    targets = [dst for _, dst in plan]
    if len(set(targets)) != len(targets):
        raise RuntimeError("存在重复目标文件名，已中止。")

    temp_plan = []
    for idx, (src, dst) in enumerate(plan, start=1):
        tmp = src.with_name(f".__tmp_rename_{timestamp}_{idx:03d}{src.suffix}")
        temp_plan.append((src, tmp, dst))

    for src, tmp, _ in temp_plan:
        src.rename(tmp)
    for _, tmp, dst in temp_plan:
        tmp.rename(dst)

    log_path = TARGET_DIR / f"rename_log_{timestamp}.txt"
    lines = ["原文件名\t新文件名"]
    lines += [f"{src.name}\t{dst.name}" for src, _, dst in temp_plan]
    log_path.write_text("\n".join(lines), encoding="utf-8")

if __name__ == "__main__":
    main()
```

## Pitfalls

- ❌ 不要直接循环 `src.rename(dst)`，容易因目标名冲突导致半改名状态。
- ❌ 不要把“未匹配”的文件强行编号；应保留并报告。
- ❌ 不要依赖文件系统修改时间判断会议/文件真实时间，除非用户明确说按修改时间排序。
- ❌ 不要把工具脚本放桌面根目录。

## Verification

执行后至少核验：

```bash
python - <<'PY'
# -*- coding: utf-8 -*-
from pathlib import Path
folder = Path(r'C:\path\to\folder')
for p in sorted([x for x in folder.iterdir() if x.is_file()], key=lambda x: x.name):
    print(p.name)
PY
```

最终回复用户时说明：处理目录、处理数量、未匹配文件、脚本路径、映射日志路径。
