# 在 Windows 上创建启动/停止快捷方式（开始菜单 + 桌面）
# 用法: powershell -NoProfile -ExecutionPolicy Bypass -File scripts\create-shortcut.ps1
$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$AppName = "电商经营数据工具箱"

# 读取端口
$Port = $env:OPS_TOOLBOX_PORT
if (-not $Port -and (Test-Path (Join-Path $RootDir "config\app-config.json"))) {
    try {
        $cfg = Get-Content (Join-Path $RootDir "config\app-config.json") -Raw | ConvertFrom-Json
        if ($cfg.server.port) { $Port = [string]$cfg.server.port }
    } catch {}
}
if (-not $Port) { $Port = "8080" }

Write-Host "项目目录: $RootDir"
Write-Host "端口: $Port"
Write-Host ""

# WScript.Shell COM 对象用于创建 .lnk
$WshShell = New-Object -ComObject WScript.Shell

# ── 路径 ──
$StartMenuDir = Join-Path ([Environment]::GetFolderPath("Programs")) $AppName
$DesktopDir = [Environment]::GetFolderPath("Desktop")

# 创建开始菜单文件夹
if (-not (Test-Path $StartMenuDir)) {
    New-Item -ItemType Directory -Force -Path $StartMenuDir | Out-Null
}

# ── 启动快捷方式 ──
# 用一个 launcher 脚本：启动服务 → 等待就绪 → 打开浏览器 → 提示
$LauncherScript = Join-Path $RootDir "scripts\launch-from-shortcut.ps1"
@"
# 从快捷方式启动（由 create-shortcut.ps1 生成）
`$ErrorActionPreference = "Stop"
Set-Location "$RootDir"

function Test-ServiceReady {
    try {
        `$Response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/api/health" -UseBasicParsing -TimeoutSec 2
        return `$Response.StatusCode -eq 200
    } catch {
        return `$false
    }
}

# 已在运行时直接打开，避免重复点击导致服务重启。
if (Test-ServiceReady) {
    Start-Process "http://127.0.0.1:$Port/"
    exit 0
}

& powershell -NoProfile -ExecutionPolicy Bypass -File "$RootDir\scripts\start.ps1" 2>`$null

# 等待健康接口就绪
`$Ready = `$false
for (`$i = 1; `$i -le 30; `$i++) {
    if (Test-ServiceReady) { `$Ready = `$true; break }
    Start-Sleep -Milliseconds 500
}

if (`$Ready) {
    Start-Process "http://127.0.0.1:$Port/"
    [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms") | Out-Null
    [System.Windows.Forms.MessageBox]::Show("服务已启动，浏览器已打开。`nhttp://127.0.0.1:$Port/", "电商经营数据工具箱", "OK", "Information") | Out-Null
} else {
    [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms") | Out-Null
    [System.Windows.Forms.MessageBox]::Show("启动失败，请查看 data\logs\server.err.log", "电商经营数据工具箱", "OK", "Warning") | Out-Null
}
"@ | Set-Content -Path $LauncherScript -Encoding UTF8

# 创建「启动」.lnk
function Create-Shortcut {
    param($ShortcutPath, $TargetScript, $Description, $IconLocation)
    $lnk = $WshShell.CreateShortcut($ShortcutPath)
    $lnk.TargetPath = "powershell.exe"
    $lnk.Arguments = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$TargetScript`""
    $lnk.WorkingDirectory = $RootDir
    $lnk.Description = $Description
    $lnk.WindowStyle = 7  # Minimized
    if ($IconLocation) { $lnk.IconLocation = $IconLocation }
    $lnk.Save()
}

# 开始菜单 — 启动
$StartLnk = Join-Path $StartMenuDir "$AppName.lnk"
Create-Shortcut -ShortcutPath $StartLnk -TargetScript $LauncherScript -Description "启动 电商经营数据工具箱"

# 桌面 — 启动
$DesktopLnk = Join-Path $DesktopDir "$AppName.lnk"
if (-not (Test-Path $DesktopLnk)) {
    Create-Shortcut -ShortcutPath $DesktopLnk -TargetScript $LauncherScript -Description "启动 电商经营数据工具箱"
    Write-Host "已创建桌面快捷方式: $DesktopLnk"
}

# 开始菜单 — 停止
$StopLnk = Join-Path $StartMenuDir "$AppName-停止.lnk"
Create-Shortcut -ShortcutPath $StopLnk -TargetScript (Join-Path $RootDir "scripts\stop.ps1") -Description "停止 电商经营数据工具箱"

Write-Host ""
Write-Host "✓ 创建完成"
Write-Host ""
Write-Host "  开始菜单: $StartMenuDir"
Write-Host "    - $AppName (启动)"
Write-Host "    - $AppName-停止 (停止)"
Write-Host "  桌面: $DesktopLnk"
Write-Host ""
Write-Host "  也可将 .lnk 固定到任务栏使用。"
Write-Host "  如需重新生成，重新运行此脚本即可。"
