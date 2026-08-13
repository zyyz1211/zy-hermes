# Example: Importing XQuant开源书 into Obsidian

A worked example from when the user asked to save the open-source quantitative trading book "XQuant" into their Obsidian vault.

## Source

- Repo: https://github.com/xingwudao/xquant-beginner
- Content: 12 markdown chapters (preface + 9 chapters + getting-started + feedback)
- Images directory: `book/images/`
- File sizes: 5KB–26KB per chapter

## Commands used

```bash
# Clone (with gh-proxy for this network)
cd /tmp && git clone --depth 1 https://gh-proxy.com/https://github.com/xingwudao/xquant-beginner.git
```

## Target structure

```
D:\<知识库>\量化交易入门_XQuant\
├── README.md              # Index with wikilinks
├── 00-前言.md
├── 00-准备工作.md
├── q1-how-to-profit.md
├── q2-what-to-buy.md
├── q3-how-much.md
├── q4-when-to-trade.md
├── q5-how-to-validate.md
├── q6-avoid-overfitting.md
├── q7-execution.md
├── q8-iteration.md
├── q9-daily-work.md
├── 00-反馈与读者群.md
└── images/                # 75 images
```

## Key decisions

1. **Folder name**: `量化交易入门_XQuant` — descriptive Chinese name matching the book's theme
2. **File names**: Kept original names (`q1-how-to-profit.md`) for traceability; prefixed non-chapter files with `00-` for sorting
3. **Frontmatter**: YAML with title, source, author, url, tags (量化交易, XQuant), and no `order` field since it wasn't needed
4. **Image paths**: Repo used `../assets/` and `assets/` references → replaced with `./images/`
5. **Index**: README.md with wikilink table of contents

## Resolution of Windows/MSYS path issue

The initial attempt failed because `Path('/tmp/xquant-beginner/book')` in Windows Python resolves to `\tmp\xquant-beginner\book` (`C:\tmp\...`), not the MSYS `/tmp/`.

**Fix**: 

```python
import os
from pathlib import Path
tmp_dir = Path(os.environ.get('TMP', r'C:\Users\<user>\AppData\Local\Temp'))
book_dir = tmp_dir / "xquant-beginner" / "book"
```

## Result

13 .md files + 75 images, all with working wikilinks and image references.
