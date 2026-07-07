$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RootDir

function Write-Step {
  param([string]$Message)
  Write-Host ""
  Write-Host "==> $Message"
}

function Write-FailHint {
  Write-Host ""
  Write-Host "更新没有完成。请把上面的报错截图发给维护人员。"
  Write-Host "常见原因：没有进入项目目录、GitHub 网络不可达、本地文件被手动改动、Python 环境安装失败。"
}

function Invoke-Native {
  param(
    [string]$FilePath,
    [string[]]$Arguments
  )
  & $FilePath @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "$FilePath $($Arguments -join ' ') 执行失败，退出码：$LASTEXITCODE"
  }
}

function Get-NativeOutput {
  param(
    [string]$FilePath,
    [string[]]$Arguments
  )
  $Output = & $FilePath @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "$FilePath $($Arguments -join ' ') 执行失败，退出码：$LASTEXITCODE"
  }
  return $Output
}

trap {
  Write-FailHint
  throw
}

Write-Host "Amazon Operations Toolbox 更新开始"
Write-Host "项目目录：$RootDir"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Host "未找到 git。请先安装 Git for Windows，然后重新运行本脚本。"
  exit 1
}

if (-not (Test-Path ".git")) {
  Write-Host "当前文件夹不是 Git 仓库。请先从 GitHub 拉取项目，或进入 amazon-ops-toolbox 项目目录后再运行。"
  exit 1
}

$CurrentBranch = Get-NativeOutput "git" @("branch", "--show-current")
$CurrentCommit = Get-NativeOutput "git" @("rev-parse", "--short", "HEAD")
$RemoteUrl = & git remote get-url origin 2>$null
if (-not $RemoteUrl) {
  $RemoteUrl = "未配置 origin"
}

Write-Host "当前分支：$CurrentBranch"
Write-Host "当前版本：$CurrentCommit"
Write-Host "远程仓库：$RemoteUrl"

$LocalChanges = Get-NativeOutput "git" @("status", "--short")
if ($LocalChanges) {
  Write-Host ""
  Write-Host "检测到本地有未提交改动，暂不自动拉取，避免覆盖部署机器上的本地修改："
  $LocalChanges | ForEach-Object { Write-Host $_ }
  Write-Host ""
  Write-Host "如果这些改动只是误改，请先备份或联系维护人员处理。"
  exit 1
}

Write-Step "拉取 GitHub 最新代码"
Invoke-Native "git" @("fetch", "--prune", "--progress", "origin")
Invoke-Native "git" @("pull", "--ff-only", "--progress")

$UpdatedCommit = Get-NativeOutput "git" @("rev-parse", "--short", "HEAD")
if ($UpdatedCommit -eq $CurrentCommit) {
  Write-Host "代码已经是最新版本：$UpdatedCommit"
} else {
  Write-Host "代码已更新：$CurrentCommit -> $UpdatedCommit"
}

Write-Step "检查并更新 Python 依赖"
Invoke-Native "powershell" @("-NoProfile", "-ExecutionPolicy", "BYPASS", "-File", ".\scripts\setup-cn.ps1")

Write-Step "重启服务"
Invoke-Native "powershell" @("-NoProfile", "-ExecutionPolicy", "BYPASS", "-File", ".\scripts\stop.ps1")
Invoke-Native "powershell" @("-NoProfile", "-ExecutionPolicy", "BYPASS", "-File", ".\scripts\start.ps1")

Write-Host ""
Write-Host "更新完成。请刷新浏览器页面后重新使用系统。"
