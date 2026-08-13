# Fast Drive Analysis Pattern (applied 2026-06-23)

## Problem

Full recursive scan of `C:\Users` or `C:\Windows` via PowerShell `Get-ChildItem -Recurse` times out after 120s. The 9p driver for `/mnt/c/` traversal in WSL is also 10-50x slower than native.

## Solution

Targeted AppData-first two-pass scan — completes in <30s:

**Pass 1 — AppData\Local** (filter >500MB):
```powershell
$local = $env:LOCALAPPDATA
Get-ChildItem $local | ForEach-Object {
    $size = (Get-ChildItem $_.FullName -Recurse -ErrorAction SilentlyContinue |
             Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
    if ($size -and $size -gt 500MB) { "{0,-30} {1,8:N1} GB" -f $_.Name, ($size/1GB) }
}
```

**Pass 2 — AppData\Roaming** (filter >200MB):
```powershell
$roaming = $env:APPDATA
Get-ChildItem $roaming | ForEach-Object {
    $size = (Get-ChildItem $_.FullName -Recurse -ErrorAction SilentlyContinue |
             Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
    if ($size -and $size -gt 200MB) { "{0,-30} {1,8:N1} GB" -f $_.Name, ($size/1GB) }
}
```

## C: drive baseline (250.7 GB total)

Typical large AppData items:
- wsl: 15.9 GB (system image, do not touch)
- NVIDIA: 11.3 GB (driver, normal)
- Kingsoft (WPS): Local 3.0 GB + Roaming 1.9 GB
- Tencent (Roaming): 3.5 GB (xwechat 1.4 GB, hxtcncec 1.0 GB)
- Doubao: 2.8 GB
- Google (Chrome): 2.7 GB
- Quark: 2.0 GB
- Unity cache: 2.0 GB
- ima.copilot: 1.7 GB
- Feishu (LarkShell): Local 1.6 GB + Roaming 0.8 GB
- SodaMusic: 1.0 GB
- npm-cache: 1.0 GB
- baidu: 1.0 GB

## D: drive baseline (225.9 GB total)

Typical large items (games/apps):
- Diablo II Resurrected: 41.2 GB (game)
- Program Files: 40.0 GB (installed software)
- SlayTheSpire: 5.9 GB (game)
- ai版_v2.0: 4.4 GB (app data)
- xwechat_files: 3.6 GB (WeChat files)
- leidian: 3.5 GB (emulator)

## Real cleanup results (2026-06-23)

C: drive: Tier 1+2b freed 6.8 GB (69.7 -> 76.4 GB free). Quark+Unity freed 4.0 GB more. Total C: freed: 10.8 GB.
D: drive: User-authorized deletion of Diablo II Resurrected (41 GB) + ai版_v2.0 (4.4 GB) + leidian (3.5 GB) = 49.1 GB freed.
Combined total: 59.9 GB freed across both drives.
