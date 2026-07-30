$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RootDir

$LogDir = Join-Path $RootDir "data\logs"
$PidFile = Join-Path $RootDir "data\server.pid"
$OutLog = Join-Path $LogDir "server.out.log"
$ErrLog = Join-Path $LogDir "server.err.log"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# ---- 解析端口：环境变量 > 配置文件 > 默认 8080 ----
$Port = $env:OPS_TOOLBOX_PORT
if (-not $Port -and (Test-Path "config\app-config.json")) {
  try {
    $cfg = Get-Content "config\app-config.json" -Raw | ConvertFrom-Json
    if ($cfg.server -and $cfg.server.PSObject.Properties["port"]) {
      $Port = [string]$cfg.server.port
    }
  } catch {}
}
if (-not $Port) { $Port = "8080" }

function Stop-ServiceOnPort {
  param($Port)
  $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  if ($conn) {
    $pids = $conn.OwningProcess | Sort-Object -Unique
    foreach ($p in $pids) {
      $isServer = $false
      try {
        $cim = Get-CimInstance Win32_Process -Filter "ProcessId = $p" -ErrorAction SilentlyContinue
        if ($cim -and ($cim.CommandLine -like "*app.ops_toolbox.server*")) { $isServer = $true }
      } catch {}
      if ($isServer) {
        Write-Host "停止占用端口 $Port 的旧服务进程 PID $p"
        Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
      } else {
        throw "端口 $Port 已被其他程序占用（PID $p）。请关闭该程序，或修改 config\app-config.json 中的 server.port。"
      }
    }
    Start-Sleep -Seconds 1
  }
}

function Stop-ByPidFile {
  if (Test-Path $PidFile) {
    $pidText = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($pidText) {
      $proc = Get-Process -Id $pidText -ErrorAction SilentlyContinue
      if ($proc) {
        $isServer = $false
        try {
          $cim = Get-CimInstance Win32_Process -Filter "ProcessId = $pidText" -ErrorAction SilentlyContinue
          if ($cim -and ($cim.CommandLine -like "*app.ops_toolbox.server*")) { $isServer = $true }
        } catch { $isServer = $false }
        if ($isServer) {
          Write-Host "停止已记录进程 PID $pidText"
          Stop-Process -Id $pidText -Force -ErrorAction SilentlyContinue
          Start-Sleep -Seconds 1
        } else {
          Write-Host "PID $pidText 已存在但非本服务进程，跳过 kill，仅清理 pid 文件。"
        }
      }
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
  }
}

# ---- 兜底清理：只停止本服务进程；其他程序占用端口时明确报错 ----
Stop-ByPidFile
Stop-ServiceOnPort -Port $Port

# ---- 环境检查 ----
$VenvPython = Join-Path $RootDir ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
  Write-Host "未找到 .venv\Scripts\python.exe。请先运行：powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-cn.ps1"
  exit 1
}
$Python = $VenvPython

# ---- 健康检查 ----
function Test-ServiceReady {
  try {
    $Response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/api/health" -UseBasicParsing -TimeoutSec 2
    return $Response.StatusCode -eq 200
  } catch {
    return $false
  }
}

# ---- 启动 ----
$Arguments = @("-m", "app.ops_toolbox.server", "--port", $Port)
if ($env:OPS_TOOLBOX_HOST) { $Arguments += @("--host", $env:OPS_TOOLBOX_HOST) }

$Process = Start-Process `
  -FilePath $Python `
  -ArgumentList $Arguments `
  -WorkingDirectory $RootDir `
  -RedirectStandardOutput $OutLog `
  -RedirectStandardError $ErrLog `
  -WindowStyle Hidden `
  -PassThru

Set-Content -Path $PidFile -Value $Process.Id

# ---- 等待健康接口就绪（最多约 15 秒）----
$Ready = $false
for ($i = 1; $i -le 30; $i++) {
  if (Test-ServiceReady) { $Ready = $true; break }
  Start-Sleep -Milliseconds 500
}

if ($Ready) {
  Write-Host "Ops Toolbox 已启动，PID $($Process.Id)，端口 $Port。"
  Write-Host "服务就绪：http://127.0.0.1:$Port/  （日志: $OutLog 和 $ErrLog）"
} else {
  Write-Host "警告：健康接口在预期时间内未就绪，请查看日志：$ErrLog" -ForegroundColor Yellow
}
