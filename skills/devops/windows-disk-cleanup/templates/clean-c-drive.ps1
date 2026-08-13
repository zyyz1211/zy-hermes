# C: Drive Tiered Cleanup Script
# Tier 1: Temp files + safe caches
# Tier 2b: App Roaming caches (safe, auto-rebuild)
# Run: powershell.exe -ExecutionPolicy Bypass -File "C:\Users\<user>\.hermes\skills\devops\windows-disk-cleanup\templates\clean-c-drive.ps1"

$startFree = (Get-PSDrive C).Free
$freed = 0

function Add-Freed($bytes) { $script:freed += $bytes }

Write-Host "===== Tier 1: Temp Files & Caches ====="

# 1. User Temp
$userTemp = "$env:LOCALAPPDATA\Temp"
if (Test-Path $userTemp) {
    $before = (Get-ChildItem $userTemp -Recurse -ErrorAction SilentlyContinue |
               Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
    Remove-Item "$userTemp\*" -Recurse -Force -ErrorAction SilentlyContinue
    $after = (Get-ChildItem $userTemp -Recurse -ErrorAction SilentlyContinue |
               Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
    Add-Freed ([math]::Max(0, ($before - $after)))
}

# 2. Windows Temp
Remove-Item "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue

# 3. Recycle Bin
$rbBefore = (Get-PSDrive C).Free
Clear-RecycleBin -Force -ErrorAction SilentlyContinue
$rbAfter = (Get-PSDrive C).Free
Add-Freed ($rbAfter - $rbBefore)

# 4. npm cache (Local)
$npmCache = "$env:LOCALAPPDATA\npm-cache"
if (Test-Path $npmCache) {
    $b = (Get-ChildItem $npmCache -Recurse -ErrorAction SilentlyContinue |
          Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
    Remove-Item "$npmCache\*" -Recurse -Force -ErrorAction SilentlyContinue
    $a = (Get-ChildItem $npmCache -Recurse -ErrorAction SilentlyContinue |
          Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
    Add-Freed ([math]::Max(0, ($b - $a)))
}

# 5. Chrome cache
$chromeCache = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache"
if (Test-Path $chromeCache) {
    $b = (Get-ChildItem $chromeCache -Recurse -ErrorAction SilentlyContinue |
          Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
    Remove-Item "$chromeCache\*" -Recurse -Force -ErrorAction SilentlyContinue
    $a = (Get-ChildItem $chromeCache -Recurse -ErrorAction SilentlyContinue |
          Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
    Add-Freed ([math]::Max(0, ($b - $a)))
}

# 6. Thumbnail cache
Remove-Item "$env:LOCALAPPDATA\Microsoft\Windows\Explorer\*.db" -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "===== Tier 2b: App Roaming Caches ====="

# 1. WPS Office addons
$wpsAddons = "$env:APPDATA\kingsoft\wps\addons"
if (Test-Path $wpsAddons) {
    $b = (Get-ChildItem $wpsAddons -Recurse -ErrorAction SilentlyContinue |
          Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
    Remove-Item "$wpsAddons\*" -Recurse -Force -ErrorAction SilentlyContinue
    $a = (Get-ChildItem $wpsAddons -Recurse -ErrorAction SilentlyContinue |
          Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
    Add-Freed ([math]::Max(0, ($b - $a)))
}

# 2. SodaMusic cache
$soda = "$env:APPDATA\SodaMusic"
if (Test-Path $soda) {
    $b = (Get-ChildItem $soda -Recurse -ErrorAction SilentlyContinue |
          Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
    Remove-Item "$soda\*" -Recurse -Force -ErrorAction SilentlyContinue
    $a = (Get-ChildItem $soda -Recurse -ErrorAction SilentlyContinue |
          Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
    Add-Freed ([math]::Max(0, ($b - $a)))
}

# 3. LarkShell caches
$lark = "$env:APPDATA\LarkShell"
if (Test-Path $lark) {
    @("aha", "sdk_storage", "update") | ForEach-Object {
        $p = "$lark\$_"
        if (Test-Path $p) {
            $b = (Get-ChildItem $p -Recurse -ErrorAction SilentlyContinue |
                  Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
            Remove-Item "$p\*" -Recurse -Force -ErrorAction SilentlyContinue
            $a = (Get-ChildItem $p -Recurse -ErrorAction SilentlyContinue |
                  Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
            Add-Freed ([math]::Max(0, ($b - $a)))
        }
    }
}

# 4. Tencent mini-program caches
$tencent = "$env:APPDATA\Tencent"
@("xwechat", "hxtcncec") | ForEach-Object {
    $p = "$tencent\$_"
    if (Test-Path $p) {
        $b = (Get-ChildItem $p -Recurse -ErrorAction SilentlyContinue |
              Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
        Remove-Item "$p\*" -Recurse -Force -ErrorAction SilentlyContinue
        $a = (Get-ChildItem $p -Recurse -ErrorAction SilentlyContinue |
              Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
        Add-Freed ([math]::Max(0, ($b - $a)))
    }
}

# 5. BaiduNetdisk AutoUpdate
$baidu = "$env:APPDATA\baidu\BaiduNetdisk\AutoUpdate"
if (Test-Path $baidu) {
    $b = (Get-ChildItem $baidu -Recurse -ErrorAction SilentlyContinue |
          Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
    Remove-Item "$baidu\*" -Recurse -Force -ErrorAction SilentlyContinue
    $a = (Get-ChildItem $baidu -Recurse -ErrorAction SilentlyContinue |
          Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
    Add-Freed ([math]::Max(0, ($b - $a)))
}

# 6. WorkBuddy cache
$wb = "$env:APPDATA\WorkBuddy\Cache"
if (Test-Path $wb) {
    $b = (Get-ChildItem $wb -Recurse -ErrorAction SilentlyContinue |
          Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
    Remove-Item "$wb\*" -Recurse -Force -ErrorAction SilentlyContinue
    $a = (Get-ChildItem $wb -Recurse -ErrorAction SilentlyContinue |
          Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
    Add-Freed ([math]::Max(0, ($b - $a)))
}

Write-Host ""
Write-Host "===== Summary ====="
$endFree = (Get-PSDrive C).Free
Write-Host ("  Total freed: {0:N1} MB ({1:N1} GB)" -f ($freed/1MB), ($freed/1GB))
Write-Host ("  Before: {0:N1} GB free" -f ($startFree/1GB))
Write-Host ("  After:  {0:N1} GB free" -f ($endFree/1GB))
Write-Host ("  Free%:  {0:N1}%" -f ($endFree/((Get-PSDrive C).Used+$endFree)*100))
