---
name: hermes-maintenance
description: Analyze, clean, and optimize Hermes Agent installation — identify redundant files, free disk space, verify runtime integrity, check system/process state on Windows, and repair the persistent memory stores (MEMORY.md/USER.md format drift, char limits).
tags:
  - hermes
  - disk-cleanup
  - maintenance
  - windows
related_skills:
  - windows-disk-cleanup  # sister skill: general Windows C drive cleanup
  - hermes-agent          # protected skill: Hermes configuration & CLI
---

# Hermes Maintenance — Installation Cleanup & Optimization

Reclaim disk space from a Hermes Agent installation by identifying and removing files that are not needed at runtime.

## Trigger Conditions

- User says "清理 Hermes", "Hermes 太大了", "清理一下 Hermes 产物"
- User wants to free up space and asks about Hermes specifically
- Hermes installation is 1.5+ GB and user hasn't been contributing to the project
- Memory tool refuses writes: `Refusing to write USER.md / MEMORY.md ... wouldn't round-trip` (drift guard, issue #26045)
- System prompt shows `USER PROFILE` / `MEMORY` at 100%+ char budget, or a memory store needs consolidation
- GitHub MCP tools fail with `Authentication Failed: Bad credentials` (token check needed)

## Background: How Hermes Is Installed

Hermes can be installed via multiple methods (WinGet, pip, git clone). Each method puts the source code in different locations:

- **WinGet install** — `hermes.exe` is a PyInstaller binary at `%LOCALAPPDATA%\Microsoft\WinGet\Links\hermes.exe`. The source code is extracted to `%LOCALAPPDATA%\hermes\hermes-agent\` (redundant copy for pip editable installs).
- **Runtime source** — The actual runtime copy lives at `~\.hermes\hermes-agent\`. This is what the `.pth` file in the virtualenv points to.
- **Desktop app** — Built Electron app at `~\.hermes\hermes-agent\apps\desktop\release\win-unpacked\Hermes.exe`.

So there are often **two independent copies** of the complete hermes-agent source tree, each with their own `.git/` history.

## Workflow

### Step 1: Assess total Hermes footprint

```bash
# Check all Hermes-related directories
du -sh "$HOME/.hermes/" 2>/dev/null
du -sh "$LOCALAPPDATA/hermes/" 2>/dev/null
# Check Electron cache
du -sh "$APPDATA/hermes-desktop/" 2>/dev/null
# Check for old portable exes
find "$HOME/Desktop" -name "hermes-desktop-*.exe" 2>/dev/null
```

### Step 2: Profile each location

```bash
# Runtime source (active)
du -sh "$HOME/.hermes/hermes-agent/"*/ 2>/dev/null | sort -rh | head -15
du -sh "$HOME/.hermes/hermes-agent/".*/ 2>/dev/null | sort -rh | head -5

# Redundant copy (if exists)
du -sh "$LOCALAPPDATA/hermes/hermes-agent/"*/ 2>/dev/null | sort -rh | head -10
du -sh "$LOCALAPPDATA/hermes/hermes-agent/".*/ 2>/dev/null | sort -rh | head -5
```

### Step 3: Classify by safety

| Category | What | Safety |
|----------|------|--------|
| **Safe to delete** | `.git/` — Git history (341–666 MB), `tests/` (34–35 MB), `website/` (27–32 MB, Docusaurus docs source), `.github/` (1.1 MB, CI config) | 100% — Not needed at runtime |
| **Safe** | `.venv/` created by test commands, `node_modules/` (21 MB, desktop build deps), `__pycache__` (auto-regenerates) | Safe — Will be recreated if needed |
| **Safe** | `infographic/` (14 MB, skill assets), `plugins/` (12 MB, plugin source), `optional-skills/` (7.8 MB) | Safe — Runtime skills are loaded from `~/.hermes/skills/`, not these source trees |
| **Must keep** | `.venv/` (506 MB in runtime dir) — Python virtualenv with all dependencies | REQUIRED for Hermes to run |
| **Must keep** | `apps/desktop/release/` — Built Electron desktop app (205+ MB Hermes.exe) | REQUIRED for `hermes desktop` |
| **Must keep** | `hermes_cli/`, `tools/`, `agent/`, `gateway/`, `cron/`, `hermes_constants.py`, `run_agent.py`, etc. | REQUIRED — Runtime Python code |
| **Must keep** | `skills/` — Bundled skills | REQUIRED for skill ecosystem |

### Step 4: Execute cleanup

```bash
# --- Runtime dir (~/.hermes/hermes-agent/) ---

# Git history (biggest win)
rm -rf "$HOME/.hermes/hermes-agent/.git"

# Test/doc/CI files
rm -rf "$HOME/.hermes/hermes-agent/tests"
rm -rf "$HOME/.hermes/hermes-agent/website"
rm -rf "$HOME/.hermes/hermes-agent/.github"

# Unused source trees
rm -rf "$HOME/.hermes/hermes-agent/infographic"
rm -rf "$HOME/.hermes/hermes-agent/plugins"
rm -rf "$HOME/.hermes/hermes-agent/optional-skills"
rm -rf "$HOME/.hermes/hermes-agent/node_modules"

# Python bytecode cache (auto-regenerates)
find "$HOME/.hermes/hermes-agent" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find "$HOME/.hermes/hermes-agent" -name "*.pyc" -delete 2>/dev/null

# --- Redundant copy (WinGet extraction) ---
if [ -d "$LOCALAPPDATA/hermes/hermes-agent" ]; then
  rm -rf "$LOCALAPPDATA/hermes/hermes-agent"
fi

# --- Old portable executables on desktop ---
rm -f "$HOME/Desktop/09_工具脚本/hermes-desktop-*.exe"

# --- Electron browser caches ---
rm -rf "$APPDATA/hermes-desktop/Cache"
rm -rf "$APPDATA/hermes-desktop/GPUCache"
```

### Step 5: Verify runtime still works

```bash
hermes --version
hermes desktop --help
# If desktop packaged app exists:
hermes desktop --build-only
```

## State Verification — Checking What's Actually Running

**Critical lesson: never make confident claims about process/runtime state from a single unreliable check. Always verify from multiple angles.**

### Windows Process Inspection (git-bash/MSYS)

When checking if a Windows process is running, avoid `//FI` filters piped through grep — they can silently miss output due to encoding or case mismatch. Use **raw `tasklist` piped through `grep -i` directly**:

```bash
# ✅ RELIABLE — pipe full tasklist output through grep
tasklist 2>/dev/null | grep -i "hermes"

# ❌ UNRELIABLE — //FI filter + grep can silently fail
tasklist //FI "IMAGENAME eq Hermes.exe" 2>/dev/null | grep -i hermes || echo "not running"
```

The `//FI` filter approach can return matching lines but the subsequent `grep` may still fail to find them. Always fall back to the raw pipe.

### Desktop App vs CLI Process

Hermes Desktop spawns **multiple processes** (Electron main renderer ~400MB + child processes). Just checking for `Hermes.exe` once isn't enough — look at the full process list:

- `Hermes.exe` (capital H, 200-500MB) = Desktop GUI app
- `hermes.exe` (lowercase h, ~5MB) = CLI launcher process

```bash
# Check ALL Hermes-related processes at once
tasklist 2>/dev/null | grep -i herm
```

### Never Declare "Not Running" Without Exhaustive Check

When the user says something is running and you can't find it, the problem is YOUR check, not their claim. Always:
1. Run `tasklist` raw (no filters) piped through `grep -i`
2. Check with PowerShell as fallback
3. Ask the user what they see before concluding

### Hermes Desktop Pets

The Hermes Desktop GUI has a **Settings/Preferences panel** that can display pets/animated mascots — they do NOT require a CLI TTY. Do not tell users pets can only run in a terminal.

### GitHub MCP Token Check (runtime auth verification)

When GitHub MCP tools fail with `Authentication Failed: Bad credentials`, verify the token directly before assuming anything else:

```bash
# Token lives in config.yaml — grep the key line itself, NOT grep -A1 (that grabs the wrong line)
TOKEN=$(grep "GITHUB_PERSONAL_ACCESS_TOKEN" ~/.hermes/config.yaml | sed 's/.*: *//; s/^"//; s/"$//')
echo "length: ${#TOKEN}"
curl -s -o /dev/null -w "HTTP %{http_code}\n" -H "Authorization: Bearer $TOKEN" https://api.github.com/user
```

- HTTP 200 → token fine; problem is elsewhere (MCP server restart needed)
- HTTP 401 → token revoked/expired → user must regenerate at github.com/settings/tokens (repo scope) and you update config.yaml
- Public reads (raw.githubusercontent.com, unauthenticated api.github.com) keep working regardless — don't claim the repo is unreachable

## Memory Store Repair — MEMORY.md / USER.md

Hermes persists memory as two files: `~/.hermes/memories/MEMORY.md` (target='memory', personal notes, default limit 2200 chars) and `~/.hermes/memories/USER.md` (target='user', user profile, default limit 1375 chars). Limits are configurable via `memory.memory_char_limit` / `memory.user_char_limit`.

**Canonical format** (what the tool writes/parses): plain-text entries joined by exactly `\n§\n` (newline, §, newline). No § wrappers around entries, no blank lines between, no markdown sections. Entry content may be multiline but must not contain `\n§\n`.

**Drift guard** (issue #26045): the memory tool refuses mutations when the file doesn't round-trip — e.g. an external edit produced a `§ entry §` per-line style, markdown sections, or one giant entry that exceeds the whole-file char limit (a blob larger than the limit means flushing would truncate it). On refusal it snapshots `USER.md.bak.<ts>` and returns a remediation hint.

**Repair procedure** (sanctioned by the guard's own hint — "rewrite the file as a clean §-delimited list of entries, then retry"):
1. Read the drifted file and the `.bak.<ts>` snapshot
2. Consolidate into one entry per logical fact; compress (merge overlapping environment/tool entries, drop facts duplicated by the system prompt), keeping total ≤ char limit
3. Rewrite the file with write_file: entries joined by `\n§\n`, no leading/trailing §, no blank lines
4. Verify the tool accepts it: `memory(action='replace', old_text=<unique substring of any entry>, content=<same text>, target='user')` must return success with `entry_count` and `usage N/N chars`

Full source-level detail (delimiters, drift signals, atomic write, token diagnostics): `references/memory-store-internals.md`.

## Pitfalls

- **Two separate copies of the source tree**: WinGet installs to `%LOCALAPPDATA%\hermes\hermes-agent\`, but the runtime copy is at `~\.hermes\hermes-agent\`. The `.pth` file in `~\.hermes\hermes-agent\.venv\Lib\site-packages\hermes-agent.pth` points to the runtime copy. The WinGet copy is redundant after the runtime is set up.
- **`.venv/` in runtime dir is CRITICAL**: Do NOT delete the `.venv/` in `~/.hermes/hermes-agent/`. It contains all Python dependencies. The redundant `.venv/` in `%LOCALAPPDATA%\hermes\hermes-agent\` is safe to delete.
- **`node_modules/` is only needed for desktop builds**: If the user ever runs `hermes desktop --force-build`, npm needs these deps. For normal usage (`hermes desktop --skip-build` or stamp-matched builds), they're unnecessary.
- **Verify after delete**: Always run `hermes --version` and a quick command check after cleanup to confirm the PyInstaller binary and runtime source tree still work together.
- **Config `desktop.skip_build: true`**: After significant cleanup (especially if `node_modules/` is removed), setting this config option prevents npm install/build from being triggered on `hermes desktop`.
- **`hermes update` may restore deleted files**: The update script may re-clone or re-extract the source tree. After update, re-run the cleanup.
