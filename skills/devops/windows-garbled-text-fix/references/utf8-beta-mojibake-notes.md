# UTF-8 Beta 模式乱码修复 — 同花顺案例笔记（2026-08-10）

## 症状与诊断轨迹
用户：同花顺 委托下单 (xiadan.exe) 打开界面乱码。
第一轮诊断（只读）：
- `reg query HKLM\SYSTEM\CurrentControlSet\Control\Nls\CodePage` → ACP=65001, OEMCP=65001, MACCP=65001
  → 系统开了「Beta版：使用 Unicode UTF-8 提供全球语言支持」，这是国产软件乱码头号原因。
- 用户区域设置正常：LocaleName=zh-CN, sLanguage=CHS, InstallLanguage=0804 —— 与乱码无关。
- 安装位置：`HKLM\SOFTWARE\WOW6432Node\...\Uninstall\同花顺` → D:\<同花顺安装目录>\同花顺\bin\happ.exe
  （委托下单程序在 D:\<同花顺安装目录>\同花顺\transaction\xiadan.exe）

## 修复执行
普通终端 reg add 报 "Access is denied"（无管理员权限）→ 改用 UAC 提权：
1. write_file 写 fix_acp.ps1（reg add ACP/OEMCP=936, MACCP=10008）
2. `powershell.exe -NoProfile -Command "Start-Process powershell -Verb RunAs -Wait -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','...fix_acp.ps1'"`
   → 弹 UAC 框，用户点「是」后执行成功。
3. 验证：ACP=936, OEMCP=936, MACCP=10008 ✓

## 关键教训 1：代码页改动必须重启才生效
用户重启前报告"还是没有修复"。查 `(Get-CimInstance Win32_OperatingSystem).LastBootUpTime`
= 2026-07-23 08:09 —— 系统根本没重启过，936 尚未加载。
→ 凡是改代码页，必须显式告知"重启电脑"这一步，且用户报"没修好"时先查 LastBootUpTime。

## 关键教训 2：文件名乱码是固化损坏，改注册表救不回
用户随后指出桌面快捷方式名 `ί�н���.lnk` 乱码。Python 分析码点：
- 'ί�н���' = [0x3af, 0xfffd, 0x43d, 0xfffd, 0xfffd, 0xfffd]
- 0xfffd = U+FFFD 替换符 = 原始 GBK 字节在 UTF-8 解码时丢失，**不可逆**，无法还原中文名。

进一步用 pywin32 读 .lnk 内部目标：
- 损坏 lnk 的 TargetPath = 空（内部存的 `D:\<同花顺安装目录>\ͬ��˳Զ����\transaction\xiadan.exe` 是乱码路径，双击必失败）
- 桌面另有「委托交易.lnk」（正常）→ TargetPath = `D:\<同花顺安装目录>\同花顺\transaction\xiadan.exe`（真实路径，存在）
- 处理：删除损坏 lnk（桌面 + 开始菜单 Programs 各一个），保留正常「委托交易.lnk」。

## 工具坑（本案例踩过）
1. `python /c/Users/...` 报错 → Windows Python 必须用 `C:/Users/...` 路径。
2. bash heredoc 写 Python 被 terminal 判定为 `&` 后台命令拒执行 → 改为 write_file + python 运行。
3. .ps1 脚本里写中文路径字面量 → PowerShell 5.1 按 ANSI 读脚本，中文变乱码，CreateShortcut 返回空对象
   → 改用 pywin32（Python 内部 Unicode）+ os.listdir 枚举文件名，绕开编码问题。
4. PowerShell 终端输出中文也乱码（GBK 控制台）→ 读 .lnk 目标优先用 pywin32 或把结果写文件。

## 最终状态
- 注册表 936/936/10008 ✓
- 损坏快捷方式已删（桌面 + 开始菜单）✓
- 桌面「委托交易.lnk」完好指向真实程序 ✓
- 待用户重启电脑后同花顺界面乱码消失。
