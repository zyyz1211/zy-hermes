---
name: knowledge-base-ingestion
description: Import external content (books, docs, repos) into the user's local knowledge base (Obsidian, Notion, etc.) with proper formatting, frontmatter, and cross-links.
platforms: [linux, macos, windows]
---

# Knowledge Base Ingestion

Import external content — an open-source book, a documentation site, a GitHub repo of notes — into the user's local knowledge management system.

## Trigger

User says "save this to my knowledge base/Obsidian" referencing external content (a URL, a repo, a book).

## Discovery phase

Before writing anything, determine:

1. **Source location** — Is it a GitHub repo? A website? A published book?
2. **Content format** — Markdown? HTML? PDF? Jupyter Notebooks?
3. **Target system** — Obsidian? Notion? Plain markdown files?
4. **Scope** — Whole repo, specific chapters, or key excerpts?

## General workflow

### 1. Acquire the content

- **GitHub repo**: `git clone --depth 1 <url>` (use `--depth 1` to avoid pulling history)
  - On networks where GitHub HTTPS is blocked, prepend `https://gh-proxy.com/` to the clone URL
- **Website**: Use `web_extract` to get clean markdown
- **Published book site**: Check for HTML/PDF download endpoints, or extract chapter by chapter

### 2. Resolve the target path

For Obsidian, use the existing vault path convention (see obsidian skill). Resolve via:
1. `OBSIDIAN_VAULT_PATH` env var
2. Fallback `~/Documents/Obsidian Vault`
3. Windows: `%APPDATA%/obsidian/obsidian.json` → `vaults.*.path`

For other systems, ask the user for the target directory.

### 3. Create the folder structure

```python
target = vault / "Descriptive-Folder-Name"
target.mkdir(parents=True, exist_ok=True)
(img_dir := target / "images").mkdir(exist_ok=True)
```

### 4. Process each content file

For each markdown source file:

```python
content = src.read_text(encoding='utf-8')

# a) Fix relative paths for images/attachments
#    Inspect the source's image references first, then replace:
content = content.replace("../assets/", "./images/")
# ... more repo-specific fixes

# b) Add YAML frontmatter
frontmatter = f"""---
title: "{title}"
source: "{source_name}"
author: "{author}"
url: "{source_url}"
tags: [tag1, tag2]
order: {n}
---
"""

# c) Write
out_path.write_text(frontmatter + content, encoding='utf-8')
```

### 5. Copy media (images, diagrams)

Use `shutil.copy2()` after `rglob("*")` to preserve subdirectory structure:

```python
import shutil
for img in src_img.rglob("*"):
    if img.is_file():
        rel = img.relative_to(src_img)
        dest = img_target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(img), str(dest))
```

### 6. Create an index / MOC note

Create a `README.md` or `MOC.md` at the folder root with:

- YAML frontmatter
- Brief description
- Resource links back to original source
- Table of contents with wikilinks (for Obsidian) or relative links

### 7. Verify

Count files created and list them for the user.

## Pitfalls

### Windows/MSYS path mismatch

On Windows, the terminal runs in git-bash (MSYS). `Path('/tmp/cloned-repo')` in Windows Python resolves to `\tmp\cloned-repo` (i.e. `C:\tmp\...`), NOT the MSYS `/tmp/` which maps to the Windows user temp directory.

**Fix**: Use `os.environ.get('TMP')` to get the real Windows temp path:

```python
import os
from pathlib import Path
tmp_dir = Path(os.environ.get('TMP', r'C:\Users\<user>\AppData\Local\Temp'))
book_dir = tmp_dir / "repo-name" / "subdir"
```

### Backslash escaping in heredocs

When running Python code via `<< 'PYEOF'` heredoc, backslash sequences (`\t`, `\n`, `\x`, `\U`) cause SyntaxError even inside single-quoted heredoc delimiters because MSYS/Windows C runtime processes them.

**Fix**: Write the Python script to a `.py` file first using `write_file`, then execute it.

### Image path fixing

Inspect the source markdown carefully before blindly replacing paths. Common patterns:
- `../assets/` → `./images/`
- `book/assets/` → `./images/`
- `assets/` → `./images/`
- Some repos use `../../` relative paths — these need a different approach

### Large repos

- Always use `--depth 1` for cloning
- If images are stored in Git LFS, they won't download with `--depth 1` — warn the user

## Output conventions

- Folder name: descriptive Chinese or English, e.g. `量化交易入门_XQuant`
- File names: use the original filenames from the source, prefixed with `00-` for frontmatter/preface/glossary
- Frontmatter: always include `title`, `source`, `author`, `url`, `tags`, and optionally `order`
- Images: copy to a local `images/` subfolder alongside the notes, and fix paths to `./images/`
- Cross-links: use `[[wikilink]]` syntax for Obsidian, relative markdown links for other targets
