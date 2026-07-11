# 电商经营数据工具箱内网部署说明

## 推荐部署方式

第一阶段建议部署在公司内网里一台长期在线的电脑上，由这台电脑运行 Web 服务，其他同事通过浏览器访问：

```text
http://<服务器局域网IP>:8080/
```

适合当前阶段的原因：

- 系统不依赖大模型，不需要外部 API。
- PDF/CSV/XLSX 处理都在本机完成，业务文件不出内网。
- 代码可用 GitHub 管理，部署电脑只需要拉取代码并重启服务。
- macOS 和 Windows 都可以部署；macOS 使用 `scripts/*.sh`，Windows 使用 `scripts/*.ps1`。

## 服务器电脑需要准备

1. 一台长期在线的电脑，建议固定局域网 IP。
2. Python 3.11 或 3.12。
3. Git。
4. 能访问项目所在 GitHub 仓库。
5. 防火墙允许同事访问 TCP `8080` 端口。

## 首次部署

macOS 服务器电脑上执行：

```bash
git clone <your-github-repo-url> 电商经营数据工具箱
cd 电商经营数据工具箱
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

Windows PowerShell 执行：

```powershell
git clone <your-github-repo-url> 电商经营数据工具箱
cd 电商经营数据工具箱
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

复制并调整配置文件。

macOS：

```bash
cp config/app-config.example.json config/app-config.json
```

Windows PowerShell：

```powershell
Copy-Item config\app-config.example.json config\app-config.json
```

重点检查这些配置：

- `server.host`：公司内网访问建议使用 `0.0.0.0`。
- `server.port`：默认 `8080`，如端口冲突可改。
- `paths.allowed_input_roots`：只把允许扫描的业务文件夹加入白名单。
- `limits.max_upload_mb`：按团队单批文件大小调整。
- `backups.backup_root`：建议放到本机固定目录或公司同步盘目录。

Windows 路径建议使用正斜杠，避免 JSON 转义问题：

```json
"allowed_input_roots": [
  "C:/AmazonData",
  "D:/Operations/Amazon"
]
```

首次启动前，强烈建议设置默认管理员密码。

macOS：

```bash
export OPS_TOOLBOX_ADMIN_PASSWORD='替换成强密码'
```

Windows PowerShell：

```powershell
$env:OPS_TOOLBOX_ADMIN_PASSWORD = "替换成强密码"
```

然后启动。

macOS：

```bash
bash scripts/start.sh
```

Windows PowerShell：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

服务会读取 `config/app-config.json` 中的监听地址和端口。同事可以用服务器电脑的局域网 IP 访问。

## 开机自启动和每日备份

macOS 服务器电脑上执行一次：

```bash
bash scripts/install-launchd.sh
```

安装后：

- 服务会在当前登录用户进入系统时自动启动。
- 每天 02:30 自动执行一次备份。
- 自启动日志在 `data/logs/launchd.out.log` 和 `data/logs/launchd.err.log`。
- 备份日志在 `data/logs/backup.out.log` 和 `data/logs/backup.err.log`。

macOS 手动备份：

```bash
bash scripts/backup.sh
```

Windows 服务器电脑上执行一次：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-windows-task.ps1
```

安装后：

- 登录当前 Windows 用户后自动启动服务。
- 每天 02:30 自动执行一次备份。
- 输出日志在 `data\logs\server.out.log`。
- 错误日志在 `data\logs\server.err.log`。

Windows 手动备份：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backup.ps1
```

## 日常启动和停止

macOS 启动：

```bash
bash scripts/start.sh
```

macOS 停止：

```bash
bash scripts/stop.sh
```

Windows 启动：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

Windows 停止：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\stop.ps1
```

日志：

```text
data/logs/server.log
data/logs/server.out.log
data/logs/server.err.log
```

## 更新代码

首次部署或尚未安装网页更新功能时，需要在部署机手动执行一次下方更新脚本。之后管理员可在“系统设置 → 系统更新”中检查并应用新版本。

网页更新会根据部署系统自动选择：

- macOS/Linux：`scripts/update.sh`
- Windows：`scripts/update.ps1`

更新前会拒绝有未提交改动或分支分叉的部署目录，更新过程会重启服务。执行记录保存在 `data/logs/web-update.log`。

推荐流程：

1. 在开发电脑完成修改和测试。
2. 提交并推送到 GitHub。
3. 到服务器电脑执行更新脚本。

macOS：

```bash
cd 电商经营数据工具箱
bash scripts/update.sh
```

Windows PowerShell：

```powershell
cd 电商经营数据工具箱
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\update.ps1
```

更新脚本会按顺序执行：

- `git pull --ff-only`
- 安装或更新 Python 依赖
- 停止旧服务
- 启动新服务

## 日常使用

1. 管理员打开浏览器访问 `http://<服务器局域网IP>:8080/`。
2. 管理员在“设置”里新增操作员账号。
3. 操作员登录后，按模块处理货件 PDF、交易报告 PDF、交易明细 CSV/XLSX。
4. 处理结果表格支持搜索、按列筛选、排序和导出。
5. 历史任务会保存到 SQLite，服务重启后仍可查看。

## 数据目录

运行数据都在：

```text
data/
  app.sqlite3       历史任务、导出记录、操作日志
  users.json        用户和密码哈希
  uploads/          用户上传的 PDF
  outputs/          导出的 CSV、Excel、zip
  backups/          每日备份压缩包
  logs/             服务日志
  server.pid        当前服务进程号
```

这些文件不应该提交到 GitHub。

## 备份建议

至少定期备份：

```text
data/app.sqlite3
data/users.json
data/outputs/
```

如果上传的原始文件也需要留档，再备份：

```text
data/uploads/
```

## 当前限制

- 当前是 HTTP 内网访问，没有 HTTPS。只建议放在可信局域网，不建议直接暴露到公网。
- 默认管理员 `admin` 只应作为初始化账号使用，部署后应立即改密码或创建正式管理员账号。
- 扫描服务器文件夹只允许 `config/app-config.json` 中的白名单目录，正式部署时应按公司电脑实际目录调整。

## 后续增强建议

优先级最高：

1. 用 Docker 固化运行环境。
2. 增加 Nginx 反向代理和 HTTPS。
3. 增加更细的权限，例如只允许管理员重命名、打包或管理扫描目录。
