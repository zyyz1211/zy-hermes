---
name: windows-disk-cleanup
description: Analyze and clean Windows C drive disk space from WSL - tiered cleanup, safe vs risky classification.
tags:
  - disk-cleanup
  - windows
  - system-maintenance
related_skills:
  - c-drive-cleanup     # absorbed into this skill (cron schedule + template script)
  - windows-software-removal  # sister skill: uninstall + residual cleanup
---

# Windows Disk Cleanup (C: / D: / any drive)

Precise, tiered process for reclaiming disk space on Windows drives (C:, D:, etc.) while working from a WSL environment. Each tier corresponds to a risk level. Covers both cache cleanup (C: AppData) and large-data removal (D: games/apps).

## Trigger Conditions

- User says "C盘满了", "磁盘空间不足", "清理C盘", "瘦身", "clean up space", "看看D盘", "清理D盘"
- User says "卸载软件", "uninstall", "删除残留", "remove program", "清理注册表残留"
- Disk free space drops below 15% of total capacity
- A large file download or system update operation fails with "disk full"

## Workflow

### Step 1: Quick overview (one-liner from WSL)

Check the specific drive the user mentioned, or all drives:

```bash
# Check C: drive
powershell.exe -Command "$c = Get-PSDrive C; \"C: Total: \" + [math]::Round(($c.Used+$c.Free)/1GB,1) + \" GB  Free: \" + [math]::Round($c.Free/1GB,1) + \" GB  Free%: \" + [math]::Round($c.Free/($c.Used+$c.Free)*100,1) + \"%\""

# Check D: drive
powershell.exe -Command "$d = Get-PSDrive D -ErrorAction SilentlyContinue; if($d){ \"D: Total: \" + [math]::Round(($d.Used+$d.Free)/1GB,1) + \" GB  Free: \" + [math]::Round($d.Free/1GB,1) + \" GB  Free%: \" + [math]::Round($d.Free/($d.Used+$d.Free)*100,1) + \"%\" } else { \"D: drive not found\" }"
```

### Step 2: Find top space consumers (fast targeted scan)

**IMPORTANT**: Never run `Get-ChildItem -Recurse` on `C:\\Users` or `C:\\Windows` top-level — it **times out** (>120s). Use the targeted AppData-first two-pass approach instead (completes in <30s).

#### For C: drive — AppData-first targeted scan

**Pass 1 — AppData\\Local subdirs** (where 90% of reclaimable space lives):
```powershell
$local = $env:LOCALAPPDATA
Get-ChildItem $local | ForEach-Object {
    $size = (Get-ChildItem $_.FullName -Recurse -ErrorAction SilentlyContinue |
             Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
    if ($size -and $size -gt 500MB) { "{0,-30} {1,8:N1} GB" -f $_.Name, ($size/1GB) }
}
```

**Pass 2 — AppData\\Roaming subdirs**:
```powershell
$roaming = $env:APPDATA
Get-ChildItem $roaming | ForEach-Object {
    $size = (Get-ChildItem $_.FullName -Recurse -ErrorAction SilentlyContinue |
             Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
    if ($size -and $size -gt 200MB) { "{0,-30} {1,8:N1} GB" -f $_.Name, ($size/1GB) }
}
```

**Pass 3 — WSL-side caches**:
```bash
du -sh ~/.cache/uv/ ~/.cache/pip/ ~/.cache/huggingface/ ~/.npm/ 2>/dev/null
```

**Pass 4 — Desktop/Downloads/Documents quick check**:
```bash
powershell.exe -Command "function Get-FolderSize(`$p) { if (Test-Path `$p) { `$s=(Get-ChildItem `$p -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum; if(`$s){return `$s}}; return 0 }; \"Desktop: {0:N1} GB\" -f ((Get-FolderSize \"`$env:USERPROFILE\Desktop\")/1GB); \"Downloads: {0:N1} GB\" -f ((Get-FolderSize \"`$env:USERPROFILE\Downloads\")/1GB); \"Documents: {0:N1} GB\" -f ((Get-FolderSize \"`$env:USERPROFILE\Documents\")/1GB)"
```

#### For D: or other drives — top-level folder scan

Non-system drives can be scanned efficiently at the top level (one level of recursion, no timeout risk):

```powershell
$drive = "D:"  # change as needed
Get-ChildItem "$drive\" -ErrorAction SilentlyContinue | Where-Object { $_.PSIsContainer } | ForEach-Object {
    $size = (Get-ChildItem $_.FullName -Recurse -ErrorAction SilentlyContinue |
             Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
    if ($size -and $size -gt 100MB) {
        "{0,-30} {1,8:N1} GB" -f $_.Name, ($size/1GB)
    }
}
```

D: drive typical findings on this machine: games (Diablo II Resurrected 41 GB, SlayTheSpire 6 GB), emulators (leidian 3.5 GB), Program Files (40 GB), WeChat files (xwechat_files 3.6 GB), and app data (ai版_v2.0 4.4 GB).

**Run from a .ps1 file** (avoids bash clobbering $ and backtick issues):
1. Write script via `write_file` to `C:\Users\<user>\Desktop\disk_analysis.ps1`
2. Verify encoding: `file /mnt/c/Users/<user>/Desktop/disk_analysis.ps1` (should show ASCII/UTF-8, not "data")
3. Execute: `powershell.exe -ExecutionPolicy Bypass -File "C:\Users\<user>\Desktop\disk_analysis.ps1"`

**Reference**: `references/fast-analysis-pattern.md` has the exact scan commands used in a real cleanup session.

### Step 3: Tiered cleanup (execute in order)

#### Tier 1 -- Safe (temp/cache only, no data loss)

| Target | Command | Typical reclaim |
|--------|---------|:--------------:|
| User Temp | `rm -rf /mnt/c/Users/*/AppData/Local/Temp/* 2>/dev/null` | 0.5-3 GB |
| Windows Temp | `powershell.exe "Remove-Item 'C:\Windows\Temp\*' -Recurse -Force -ErrorAction SilentlyContinue"` | 0-2 GB |
| npm cache (Local) | `powershell.exe "Remove-Item '$env:LOCALAPPDATA\npm-cache\*' -Recurse -Force -ErrorAction SilentlyContinue"` | **0.5-1.5 GB** |
| pip cache | `rm -rf ~/.cache/pip/* 2>/dev/null` | 0.2-1 GB |
| uv cache | `rm -rf ~/.cache/uv/* 2>/dev/null` | 2-10 GB |
| npm cache (WSL) | `rm -rf ~/.npm/* 2>/dev/null` | 0.1-0.5 GB |
| HF cache | `rm -rf ~/.cache/huggingface/* 2>/dev/null` | 0.5-5 GB |
| Thumbnail cache | `rm -rf /mnt/c/Users/*/AppData/Local/Microsoft/Windows/Explorer/*.db 2>/dev/null` | 0-0.1 GB |
| Recycle Bin | `powershell.exe "Clear-RecycleBin -Force" 2>/dev/null` | 0-5 GB |
| Node-gyp cache | `rm -rf ~/.cache/node-gyp/* 2>/dev/null` | 0-0.1 GB |

**Tier 1 typically reclaims 5-15 GB** on a moderately used machine.

#### Tier 2 -- Usually safe (may inconvenience)

| Target | Command | Notes |
|--------|---------|-------|
| Windows Update cache | `rm -rf /mnt/c/Windows/SoftwareDistribution/Download/* 2>/dev/null` | Next update re-downloads; ~1 GB |
| Chrome cache | `rm -rf /mnt/c/Users/*/AppData/Local/Google/Chrome/User Data/Default/Cache/* 2>/dev/null` | 0.3-2 GB |
| Edge cache | Similar path under `Microsoft\\Edge\\User Data` | 0.1-1 GB |

#### Tier 2b -- App Roaming caches (safe, app auto-rebuilds)

These are the biggest hidden space hogs in `%APPDATA%` (Roaming). Each can be cleaned without data loss:

| App | Path | Common size | What it is |
|-----|------|:-----------:|------------|
| **WPS Office** | `%APPDATA%\kingsoft\wps\addons\` | **4-5 GB** | Downloadable template/material packages — app re-downloads on demand |
| **SodaMusic (汽水音乐)** | `%APPDATA%\SodaMusic\` | **3-5 GB** | Offline music cache — will re-cache played songs |
| **Lark/Feishu (飞书)** | `%APPDATA%\LarkShell\aha\` + `\sdk_storage\` + `\update\` | **2-3 GB** | Cached messages/attachments + update packages |
| **Quark (夸克)** | `%LOCALAPPDATA%\Quark\User Data\` | **2-3 GB** | Browser cache/profile — safe to wipe, app rebuilds |
| **Unity cache** | `%LOCALAPPDATA%\Unity\cache\` | **1-2 GB** | Unity editor asset cache — safe unless actively developing |
| **WeChat Mini Programs** | `%APPDATA%\Tencent\xwechat\` | **1-2 GB** | Mini-program cache within WeChat |
| **BaiduNetdisk (百度网盘)** | `%APPDATA%\baidu\BaiduNetdisk\AutoUpdate\` | **1-2 GB** | Update installation packages |
| **Tencent components** | `%APPDATA%\Tencent\hxtcncec\` | **0.5-1.5 GB** | Various Tencent app component caches |
| **WorkBuddy** | `%APPDATA%\WorkBuddy\Cache\` | 0.5-1 GB | Cached workspace data |

**Discovery pattern**: When `%APPDATA%` shows as 15-25+ GB, drill down by listing top subdirectories:
```powershell
$roaming = $env:APPDATA
Get-ChildItem $roaming | ForEach-Object {
    $size = (Get-ChildItem $_.FullName -Recurse -ErrorAction SilentlyContinue |
             Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
    if ($size -and $size -gt 100MB) {
        "{0,-25} {1,8:N1} GB" -f $_.Name, ($size/1GB)
    }
}
```
Then for each top consumer, drill into its subdirs to find the actual cache/data split.

**Cleanup strategy**: Delete from PowerShell while in WSL:
```powershell
powershell.exe -ExecutionPolicy Bypass -Command "Remove-Item '$env:APPDATA\kingsoft\wps\addons\*' -Recurse -Force -ErrorAction SilentlyContinue"
```
Write a `.ps1` script to the Windows desktop and run it with `powershell.exe -File` -- avoids bash escaping issues with `$` and backticks. After writing a `.ps1` script with `write_file`, verify the encoding:
```bash
file /mnt/c/Users/<user>/Desktop/script.ps1
# Should show: "ASCII text" or "UTF-8 text"
# If it shows "data" (binary/null bytes), rewrite via cat heredoc or Python open()
```

**Tier 2b typically reclaims 6-15 GB** on a machine with WPS/Lark/Tencent apps.

#### Tier 2c — Non-essential app data (ask user before cleaning)

After Tier 1+2b, present the remaining large AppData items >1 GB to the user and ask which they'd like to clear. Common candidates:

| App | Path | Typical size | Note |
|-----|------|:-----------:|------|
| **Quark (夸克)** | `%LOCALAPPDATA%\Quark\User Data` | 2-3 GB | Browser profile/cache — safe to delete, app rebuilds |
| **Unity** | `%LOCALAPPDATA%\Unity\cache` | 1-2 GB | Asset cache — safe unless actively developing |
| **Doubao (豆包)** | `%LOCALAPPDATA%\Doubao` | 2-3 GB | AI assistant cache/data |
| **ima.copilot** | `%LOCALAPPDATA%\ima.copilot` | 1-2 GB | Tencent AI copilot cache |

Pattern: after the automated cleanup, present a concise summary of remaining 1GB+ items with a clear ask — "X, Y, Z can also be cleaned, want me to clear them?"

**Cleanup command (after user confirms)**:
```powershell
Remove-Item "$env:LOCALAPPDATA\Quark\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:LOCALAPPDATA\Unity\cache\*" -Recurse -Force -ErrorAction SilentlyContinue
```

### Step 3b: Cron job pattern (set it and forget it)

Use `cronjob` to schedule recurring cleanup:
- Schedule: `0 9 */14 * *` (every 2 weeks at 9 AM)
- Load the `windows-disk-cleanup` skill
- Run the PowerShell cleanup script
- Report results back to the user

**⚠️ IMPORTANT — when absorbing another skill**: If this skill absorbs/renames from an older skill (e.g. `c-drive-cleanup` → `windows-disk-cleanup`), you MUST update any existing cron jobs that still reference the old skill's template path. Steps:
1. `cronjob action=list` to find all jobs — check their prompts for old paths
2. `cronjob action=update job_id=<id> prompt=<new prompt>` to fix each one
3. Verify the script file exists at the new `templates/` path first
4. `cronjob action=run job_id=<id>` to confirm it works after the fix
Skipping this step means the cron job silently fails with a file-not-found error next time it fires.

Write the Tier-1+Tier-2b cleanup commands into a `.ps1` file under the skill's `templates/` directory so the cron job can invoke it directly:

```bash
# From WSL, trigger the cron
powershell.exe -ExecutionPolicy Bypass -File "C:\Users\<user>\.hermes\skills\devops\windows-disk-cleanup\templates\clean-c-drive.ps1"
```

The template script (`templates/clean-c-drive.ps1`) does:
1. Wipe Tier-1 targets (Temp, RecycleBin, npm-cache, Chrome cache, thumbnails)
2. Wipe Tier-2b AppData targets (WPS addons, SodaMusic, LarkShell aha/sdk_storage/update, Tencent xwechat/hxtcncec, BaiduNetdisk AutoUpdate, WorkBuddy cache)
3. Report total freed bytes + remaining C drive capacity
4. Flush stdout to avoid buffering in cron context

For non-User directories (Quark, Unity cache), the script does NOT include them — ask the user first before removing those.

#### Tier 3 -- Safe when old (use Dism, not direct deletion)

| Target | Command | Notes |
|--------|---------|-------|
| WinSxS old | `Dism.exe /Online /Cleanup-Image /StartComponentCleanup` | Can reclaim 5-10 GB from WinSxS |
| Previous Windows | `Dism.exe /Online /Cleanup-Image /StartComponentCleanup /ResetBase` | Only if no need to uninstall latest update |
| Windows.old | `Remove-Item 'C:\Windows.old' -Recurse -Force` | Only after confirming new system stable |
| Old drivers | `pnputil /enum-drivers` then remove old | Advanced -- skip for routine |

### Step 4: Multi-agent delegation pattern

For large C drives (250+ GB), delegate parallel analysis tasks to subagents:

```python
delegate_task(tasks=[
    {"goal": "Analyze C: drive top-level directories via PowerShell", ...},
    {"goal": "Find all files >100MB on C: drive, top 30 by size", ...},
    {"goal": "Execute Tier-1 cleanup (Temp/caches/RecycleBin) and report bytes freed", ...},
])
```

## Pitfalls

- **Full C: drive recursion via `Get-ChildItem -Recurse` on `C:\Users` or `C:\Windows` TIMES OUT** (>120s). Never scan top-level dirs recursively. Use the targeted AppData-first approach (Step 2) which completes in <30s.
- **PowerShell from WSL**: `$` and backticks get consumed by bash. Write scripts to `.ps1` files first, then run with `powershell.exe -File`. Or use single-quoted `-Command` strings with careful escaping.
- **`du` over `/mnt/c/` is SLOW** -- traversing the Windows filesystem through the WSL 9p driver is 10-50x slower than native PowerShell. Use PowerShell `Get-ChildItem -Recurse` for Windows paths.
- **Permission errors are normal** on `C:\Windows`, `C:\ProgramData`, protected system folders. Use `-ErrorAction SilentlyContinue` and ignore them.
- **locked temp files**: Some Temp files are in-use by running processes. `rm -rf` skips what it can't delete -- that's fine.
- **HF_ENDPOINT**: In Chinese networks, HuggingFace (huggingface.co) is often blocked. Set `export HF_ENDPOINT=https://hf-mirror.com` before any HF model download.
- **WSL network on wake**: If "Network is unreachable" appears during cleanup, restart WSL from Windows PowerShell: `wsl --shutdown` then re-enter. See `fix-wsl-network.ps1` on the user's Desktop.
- **WinSxS**: Never delete WinSxS directly -- always use `Dism.exe` or Windows Disk Cleanup tool.
- **User data in Roaming**: `%APPDATA%` often contains large WeChat/QQ file caches (25+ GB). These are user data, not caches — ask before cleaning.

**Deep Roaming analysis technique**: When `AppData\Roaming` tops the charts, the standard `Get-ChildItem` may miss large data if `Measure-Object -Property Length` fails on directory-only entries. Use a sub-function that catches errors:

```powershell
function Get-FolderSize($path) {
    $size = (Get-ChildItem $path -Recurse -ErrorAction SilentlyContinue |
             Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
    return $size
}
```

Then drill into each top consumer's subdirectories separately to find the actual cache/data split. Key insight: many apps store their data in the root app folder (e.g. `kingsoft\wps\addons\*` for 4.8 GB of templates), not in a named "cache" subdirectory.

**Common misleading item**: `Tencent` folder in `%APPDATA%` (3+ GB) — if WeChat files are configured to save on D: drive, the Roaming\Tencent folder still contains mini-program caches (`xwechat` ~1.5 GB) and component caches (`hxtcncec` ~1 GB), neither of which are user documents.
- **Run scripts from WSL**: If you use `write_file` to create a `.ps1` on desktop, first check the file encoding is UTF-8 (not UTF-16). Use `file` command to verify.

## Verification

After cleanup, re-run Step 1 to confirm freed space:
```powershell
$c = Get-PSDrive C
"Free: " + [math]::Round($c.Free/1GB,1) + " GB"
```
