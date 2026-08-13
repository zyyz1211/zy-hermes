# 同花顺 彻底卸载案例

## 原始信息

- 产品名：同花顺 (HevoB2C)
- 版本：10.1.1.2
- 安装目录：`C:\同花顺`
- 注册表键：`HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\同花顺`
- 卸载程序：`C:\同花顺\bin\HevoUninst\HevoUninst.exe`
- 相关进程：`hxdaemonprocess.exe`, `updater.exe`（在 `bin\hxdaemonprocess\` 和 `bin\Updateworking\` 下）
- 相关域名：`10jqka.com.cn`（同花顺母公司），`voyager.hevo.10jqka.com.cn`

## 卸载过程要点

### 官方卸载失败

```
卸载退出码: -2147450740 (0x8000FFFF — Catastrophic Failure)
```

卸载器为 .NET 应用（HevoUninst.dll + hostfxr），静默参数 `/S` 无效。最终判断为 GUI 卸载器崩溃。

### 目录结构

```
C:\同花顺\
├── bin\
│   ├── hxdaemonprocess\
│   │   ├── hxdaemonprocess.exe   ← 后台守护进程
│   │   └── hdpgms.dll
│   ├── Updateworking\
│   │   ├── updater.exe           ← 更新进程
│   │   └── logger\
│   │       └── update.log        ← 被占用导致 rmdir 失败
│   └── HevoUninst\               ← 卸载程序
├── cache\
└── transaction\
```

### 关键命令

```sh
# 获取所有权+权限→删除
cmd.exe /c "takeown /f C:\同花顺 /r /d y && icacls C:\同花顺 /grant Administrators:F /t /q && rmdir /s /q C:\同花顺"

# 注册表清理（提权）
Start-Process -FilePath 'reg.exe' -ArgumentList 'delete "HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\同花顺" /f' -Verb RunAs -Wait
```

### 用户数据检查结果

- `%LOCALAPPDATA%\同花顺` — 不存在
- `%APPDATA%\同花顺` — 不存在
- `%USERPROFILE%\.hevo` — 不存在
- `%USERPROFILE%\Documents\同花顺` — 不存在
- 桌面/开始菜单快捷方式 — 不存在
