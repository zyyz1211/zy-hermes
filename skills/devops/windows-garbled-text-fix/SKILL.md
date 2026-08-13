---
name: windows-garbled-text-fix
description: 修复 Windows 中文乱码问题——国产软件界面乱码（同花顺/券商客户端等）、文件名/快捷方式乱码、GBK vs UTF-8 代码页冲突。当用户报"软件打开是乱码"、"文件名乱码"、"快捷方式乱码"或改过系统区域设置后出现乱码时使用。含注册表代码页诊断与修复、UAC 提权、重启验证、U+FFFD 损坏文件名清理、.lnk 重建。
---

# Windows 中文乱码修复

## 触发条件
- 国产软件（同花顺、券商客户端、老式财务软件等）界面文字全乱码
- 文件名/快捷方式名显示乱码（典型如 `ί�н���.lnk`、`ͬ��˳Զ����`）
- 用户反馈"还是没有修复"——先查重启状态再继续排查

## 根因速查
- 注册表 `ACP`/`OEMCP` = 65001 → 系统开启了「Beta版：使用 Unicode UTF-8 提供全球语言支持」
- 国产软件内部用 GBK 编码、不走 Unicode API → UTF-8 代码页下中文全乱码
- 区域设置本身是 zh-CN 不影响——乱码只取决于系统代码页
- 文件在 UTF-8 beta 模式期间创建时，GBK 中文被错误解码 → 乱码**固化进文件名**，改回 936 也救不回（见下）

## 诊断步骤（只读，先查再改）
1. 查代码页：`reg query "HKLM\SYSTEM\CurrentControlSet\Control\Nls\CodePage" /v ACP`（同时查 OEMCP、MACCP）。65001 = beta 开关开着；936 = GBK 正常。
2. 查是否重启过：`powershell.exe -NoProfile -Command "(Get-CimInstance Win32_OperatingSystem).LastBootUpTime"`。代码页改动**必须重启才生效**——若 LastBootUpTime 早于修改时间，用户报"没修好"是正常现象，缺重启这一步。
3. 扫描 U+FFFD 损坏文件名：运行 `scripts/scan_mojibake_files.py`（传桌面、开始菜单等路径参数）。U+FFFD（替换符）意味着原始字节已丢失，名字不可还原。
4. 查软件安装位置：`reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall" /s /f "<软件名>"`。

## 修复：改回 936
非管理员终端写 HKLM 会被拒绝（Access is denied），用 UAC 提权模式——屏幕会弹 UAC 框，**要提醒用户点「是」**：
1. 用 write_file 写一个 .ps1 修复脚本（不要 heredoc，见坑 #2）：
```powershell
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Nls\CodePage" /v ACP /t REG_SZ /d 936 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Nls\CodePage" /v OEMCP /t REG_SZ /d 936 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Nls\CodePage" /v MACCP /t REG_SZ /d 10008 /f
```
2. 执行：`powershell.exe -NoProfile -Command "Start-Process powershell -Verb RunAs -Wait -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','<脚本路径>'"`，然后 reg query 验证三项已改。
3. 明确告诉用户：**必须重启电脑**，代码页才会加载。对 WSL/Hermes/Office/微信等 Unicode 原生程序无影响。

## 已损坏的文件名/快捷方式（不可逆，只能删）
- 文件名含 U+FFFD → 中文已丢失，**无法重命名还原**，只能删除。
- .lnk 内部目标路径也可能乱码存储（如 `D:\<同花顺安装目录>\ͬ��˳Զ����\...`）→ 即使重命名文件，双击也找不到程序，必失败。
- 处理：先确认桌面/开始菜单是否有正常的同款快捷方式（用 pywin32 读 TargetPath 验证真实路径存在），有则只删损坏的；没有则用 COM 重建指向真实路径的快捷方式。
- 桌面 + 开始菜单（`AppData\Roaming\Microsoft\Windows\Start Menu\Programs`）都要扫，两处常有同款损坏副本。
- 用 pywin32 读 .lnk 目标：`win32com.client.Dispatch('WScript.Shell').CreateShortcut(path).TargetPath`。

## 工具细节与坑
1. **Windows Python 不认 MSYS 路径**：`python /c/Users/...` 报 No such file——必须用 `C:/Users/...` 形式。
2. **bash heredoc 写 Python 可能被 terminal 误判**（含 `&` 或特殊字符时报错/要求审批）——先 write_file 成 .py 再 `python "C:/..."` 运行，稳定。
3. **.ps1 里写中文路径字面量会被代码页搞乱**（PowerShell 5.1 按 ANSI 读脚本，中文变锟斤拷，CreateShortcut 拿到空对象）——改用 pywin32 + os.listdir 枚举（Python 内部 Unicode，无此问题），或给 ps1 加 UTF-8 BOM。
4. 删除 U+FFFD 文件用 Python `os.remove`（Unicode API），不要用 bash `rm`（编码易错）。
5. 提权后的 reg 修改验证要回到普通终端重新 reg query，确认三项值。

## 验证
- reg query 三项 = 936/936/10008 ✓
- LastBootUpTime 在修改时间之后（已重启）✓
- 重启后国产软件界面正常；快捷方式双击能打开真实 exe

详细案例见 `references/utf8-beta-mojibake-notes.md`。
