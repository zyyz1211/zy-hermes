---
name: windows-software-removal
description: 从 WSL/git-bash 环境彻底卸载 Windows 软件并清除残留——注册表清理、进程终止、权限获取、强制删除。
trigger: 用户要求卸载某个 Windows 软件（尤其是国产软件/SaaS客户端），或要求"彻底清除"某软件残留。
tags: [windows, uninstall, cleanup, registry, admin]
---

# Windows 软件彻底卸载

从 Hermes 运行的 WSL/git-bash 环境（非管理员）中，完整卸载 Windows 软件并清除全部残留。

## 步骤

### 1. 定位安装信息

同时查三路：

```powershell
# (A) 卸载注册表——列出安装程序及位置
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*" |
  Where-Object DisplayName -like "*软件名*" |
  Select-Object DisplayName, InstallLocation, UninstallString

Get-ItemProperty "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*" |
  Where-Object DisplayName -like "*软件名*" |
  Select-Object DisplayName, InstallLocation, UninstallString

# (B) 全盘文件搜索（shell 侧）
ls -la "/c/Program Files/"  # 包含关键词的目录
ls -la "/c/Program Files (x86)/"
ls "/c/Users/$USER/AppData/Local/"
ls "/c/Users/$USER/AppData/Roaming/"

# (C) 注册表软件键
Test-Path "HKLM:\SOFTWARE\软件名"
Test-Path "HKCU:\SOFTWARE\软件名"
```

### 2. 尝试官方卸载

优先用官方卸载程序（干净）：

```powershell
# GUI 卸载器——用 Start-Process 启动并等待
Start-Process -FilePath "uninstall.exe" -PassThru | Wait-Process

# 带静默参数的重试
Start-Process -FilePath "uninst.exe" -ArgumentList "/S" -Wait
```

### 3. 进程终止（卸载失败后）

```powershell
Get-Process -Name "进程名1","进程名2" -ErrorAction SilentlyContinue |
  Stop-Process -Force
```

### 4. 强制删除目录

从 git-bash 执行 cmd.exe 以避免 PowerShell 的权限限制：

```sh
# 先 takeown 获取所有权，再 icacls 给完全控制，最后 rmdir
cmd.exe /c "takeown /f C:\软件目录 /r /d y && icacls C:\软件目录 /grant Administrators:F /t /q && rmdir /s /q C:\软件目录"
```

> **注意**：`/c/` 的 MSYS 路径在 cmd.exe 中不工作——必须用 `C:\` 原生路径。

### 5. 注册表清理

卸载记录在 `HKLM\...\Uninstall` 下，需要管理员权限才能删除：

```powershell
# 法一：Start-Process -Verb RunAs（弹 UAC，后台可能静默失败）
Start-Process -FilePath 'reg.exe' -ArgumentList 'delete "HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\软件名" /f' -Verb RunAs -Wait

# 法二：reg.exe 直接（失败则用法一）
reg delete "HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\软件名" /f
```

软件键清理（`HKCU` 无需提权，`HKLM` 需要）：

```powershell
# HKCU 可用
Remove-Item -Path "HKCU:\SOFTWARE\软件名" -Recurse -Force

# HKLM 需提权（用法一）
```

### 6. 用户数据清理

```powershell
$userPaths = @(
    "$env:LOCALAPPDATA\软件名",
    "$env:APPDATA\软件名",
    "$env:USERPROFILE\.软件名",
    "$env:USERPROFILE\Documents\软件名"
)
foreach ($p in $userPaths) { if (Test-Path $p) { Remove-Item $p -Recurse -Force } }
```

### 7. 验证

```powershell
# 目录
Test-Path "C:\软件目录"
# 注册表
Get-ChildItem "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall" |
  ForEach-Object { Get-ItemProperty $_.PSPath } |
  Where-Object DisplayName -like "*软件名*"
# 进程
Get-Process -Name "软件相关进程名" -ErrorAction SilentlyContinue
```

## 注意事项（抗诱惑清单）

- **先在 PowerShell 而非 shell 侧搜索注册表**。国产软件的 Uninstall 注册表项常常没有 InstallLocation，但 DisplayName 一定有。
- **GUI 卸载器的退出码不可靠**。`0x8000FFFF`（-2147450740）表示 Catastrophic Failure——说明卸载器内部崩溃了，不代表卸载完成。之后仍需手动清理。
- **目录路径转义**。注册表中的路径可能是 `C:\同花顺` 这种含中文的。在 MSYS 侧用 `/c/同花顺/`；在 PowerShell/cmd 侧用原生 `C:\` 路径。
- **rmdir 失败=有进程在占用文件**。先 kill 相关进程再重试。用 cmd.exe 的 rmdir 比 PowerShell 的 Remove-Item 更直接。
- **HKLM 注册表必须提权**。`Verb RunAs` 弹 UAC 在无交互终端中可能静默失败，但后续验证可以确认。备选：用 SYSTEM 账户创建计划任务。
- **临时脚本用完即删**。清理后记得 `rm -f C:\Users\...\_temp*.ps1`。

## 相关工具

- `reg.exe` — 命令行注册表操作（比 PowerShell 更稳定）
- `takeown` / `icacls` — 获取文件所有权/权限
- `schtasks` — 以 SYSTEM 提权运行（备选方案）
