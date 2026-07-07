# Amazon Operations Toolbox

内部电商经营数据工具箱。当前阶段支持亚马逊货件外箱标 PDF 识别与规范命名、汇总报告 PDF 提取、交易明细 CSV/XLSX 汇总清洗、港杂费 PDF 提取、沃尔玛交易数据 Excel 清洗合并、导出下载、用户权限、历史任务持久化和内网部署。

## 适合谁看

- 只想把系统部署到公司电脑上的同事：看“零基础部署步骤”。
- 日常使用系统的运营同事：看“怎么打开和使用”。
- 负责后续维护代码的人：看“日常更新代码”和 `docs/lan-deployment.md`。

## 零基础部署步骤

下面分别给出 macOS 和 Windows 的部署方式。目标是：选一台公司电脑作为服务器，其他同事通过局域网浏览器访问。

### 1. 准备一台服务器电脑

建议：

- 电脑长期在线，不要经常关机。
- 连接公司内网。
- 最好给这台电脑固定局域网 IP。

### 2. 安装基础软件

macOS 打开“终端”，Windows 打开“PowerShell”，先检查是否已经安装 Git 和 Python：

```bash
git --version
python3 --version
```

Windows 如果 `python3 --version` 没反应，也可以试：

```powershell
python --version
```

如果提示找不到 `git` 或 `python3`：

- Git：可以安装 Xcode Command Line Tools，终端里执行 `xcode-select --install`。
- Windows Git：安装 [Git for Windows](https://git-scm.com/download/win)。
- Python：建议安装 Python 3.11 或 3.12。Windows 安装时勾选 “Add python.exe to PATH”。

### 3. 拉取项目代码

macOS：

```bash
cd ~/Documents
git clone https://github.com/XuKeqiang/amazon-ops-toolbox.git
cd amazon-ops-toolbox
```

Windows PowerShell：

```powershell
cd $HOME\Documents
git clone https://github.com/XuKeqiang/amazon-ops-toolbox.git
cd amazon-ops-toolbox
```

以后所有操作都在这个 `amazon-ops-toolbox` 文件夹里执行。

### 4. 安装 Python 依赖

第一次部署建议直接运行国内镜像安装脚本。脚本会检查 Python 版本、创建 `.venv` 虚拟环境、使用清华 PyPI 镜像安装依赖，并自动创建 `config/app-config.json`。

推荐 Python 3.11 或 3.12。Python 版本太旧会安装失败；系统全局 Python 和项目 `.venv` 混用也容易导致依赖缺失，所以后续启动脚本会固定使用 `.venv`。

macOS：

```bash
bash scripts/setup-cn.sh
```

Windows PowerShell：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-cn.ps1
```

如果公司网络无法访问清华镜像，可以临时换成阿里云镜像：

macOS：

```bash
PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple bash scripts/setup-cn.sh
```

Windows PowerShell：

```powershell
$env:PIP_INDEX_URL="https://mirrors.aliyun.com/pypi/simple"
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-cn.ps1
```

如果安装过程没有报错，就可以进入下一步。熟悉 Python 的维护者也可以手动创建 `.venv` 后运行 `pip install -r requirements.txt`，但日常部署优先使用上面的脚本。

### 5. 创建配置文件

如果第 4 步使用了 `setup-cn` 脚本，通常已经自动创建了 `config/app-config.json`。如果没有，再手动复制一份配置模板：

macOS：

```bash
cp config/app-config.example.json config/app-config.json
```

Windows PowerShell：

```powershell
Copy-Item config\app-config.example.json config\app-config.json
```

打开 `config/app-config.json`，重点检查：

- `server.host`：内网部署建议保持 `0.0.0.0`。
- `server.port`：默认 `8080`，端口冲突时再改。
- `paths.allowed_input_roots`：允许系统扫描的服务器文件夹白名单。
- `limits.max_upload_mb`：单次上传大小限制。

`paths.allowed_input_roots` 默认只包含项目内的 `data/input`。如果运营文件放在服务器上的其他目录，一定要改成你自己电脑或公司服务器的真实路径。系统只会扫描这个白名单里的目录，避免误读其他文件。

注意：`config/app-config.json` 是每台部署机器自己的本机配置，不会提交到 GitHub，也不会被 `git pull` 自动更新。换电脑部署时不要照搬开发者电脑路径，要改成那台服务器真实存在的目录。

macOS 路径示例：

```json
"allowed_input_roots": [
  "/Users/Shared/EcommerceData",
  "/Volumes/Operations/Amazon"
]
```

Windows 路径建议在配置里写成这种形式：

```json
"allowed_input_roots": [
  "C:/AmazonData",
  "D:/Operations/Amazon"
]
```

如果不确定怎么改，先保持默认配置也可以启动；但只能扫描项目目录下的 `data/input`。拖放上传、选择文件、选择文件夹不依赖这个白名单。

### 6. 设置管理员初始密码

第一次启动前，建议设置一个正式管理员密码：

macOS：

```bash
export AMAZON_TOOLBOX_ADMIN_PASSWORD='换成你的强密码'
```

Windows PowerShell：

```powershell
$env:AMAZON_TOOLBOX_ADMIN_PASSWORD = "换成你的强密码"
```

如果没有设置，默认管理员账号是：

```text
用户名：admin
密码：admin123
```

部署给团队使用前，建议登录后立刻在“设置”里修改或新建正式管理员账号。

### 7. 启动服务

macOS：

```bash
bash scripts/start.sh
```

Windows PowerShell：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

看到类似 “started with PID ...” 就表示服务已经启动。

本机浏览器打开：

```text
http://127.0.0.1:8080/
```

同事通过局域网访问：

```text
http://服务器电脑的局域网IP:8080/
```

查看本机局域网 IP：

macOS：

```bash
ipconfig getifaddr en0
```

Windows PowerShell：

```powershell
ipconfig
```

Windows 输出里找当前网络下的 `IPv4 地址`。macOS 如果 `ipconfig getifaddr en0` 没有输出，可以到“系统设置 → 网络”里查看当前网络的 IP 地址。

### 8. 停止服务

macOS：

```bash
bash scripts/stop.sh
```

Windows PowerShell：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\stop.ps1
```

### 9. 设置开机自启动和每日备份

确认系统能正常打开后，再执行：

macOS：

```bash
bash scripts/install-launchd.sh
```

Windows PowerShell：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-windows-task.ps1
```

安装后：

- 电脑登录后会自动启动服务。
- 每天 02:30 自动备份一次。
- 备份文件在 `data/backups/`。

也可以手动备份：

macOS：

```bash
bash scripts/backup.sh
```

Windows PowerShell：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backup.ps1
```

## 怎么打开和使用

1. 打开浏览器访问 `http://服务器电脑的局域网IP:8080/`。
2. 管理员登录后，可以在“设置”里新增操作员账号。
3. 操作员登录后，可以处理自己权限范围内的数据任务。
4. 货件 PDF 支持上传一批 PDF、拖放文件夹，或扫描服务器白名单目录。
5. 汇总报告 PDF 支持拖放 PDF、选择文件、选择文件夹，或输入服务器文件夹路径处理。
6. 亚马逊交易明细 CSV/XLSX 支持拖放文件、选择文件、选择文件夹，或输入服务器文件夹路径处理；非支持格式会在日志和审计中提示。
7. 沃尔玛交易数据支持拖放 `.xlsx/.xlsm`、选择文件、选择文件夹，或输入服务器文件夹路径处理。
8. 识别结果表格支持搜索、筛选、排序和导出。
9. 历史任务会保存到 SQLite，服务重启后仍可查看并重新下载交付物。

汇总报告 PDF 的店铺名以文件名或文件夹中推断出的店铺名为主。PDF 正文里的 `Display name` 只用于核验：如果文件名店铺名和 PDF 店铺名首字母不一致，系统会在预检日志和确认弹窗里提醒，用户确认后才继续生成 Excel。

## 日常更新代码

当 GitHub 仓库有新版本时，在服务器电脑执行：

macOS：

```bash
cd ~/Documents/amazon-ops-toolbox
bash scripts/update.sh
```

Windows PowerShell：

```powershell
cd $HOME\Documents\amazon-ops-toolbox
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\update.ps1
```

它会自动：

- 拉取最新代码
- 更新 Python 依赖
- 停止旧服务
- 启动新服务

更新完成后，建议做 3 个检查：

1. 刷新浏览器页面，确认可以正常登录。
2. 打开“汇总报告 PDF”或其他常用模块，确认页面没有旧缓存导致的异常。
3. 如果这次更新涉及 `config/app-config.example.json` 或 README 中的配置项，手动检查自己的 `config/app-config.json` 是否需要补充新配置。

`git pull` 不会覆盖 `config/app-config.json`、数据库、上传文件和导出文件。它们属于部署机器本地数据，会继续保留。

如果只想手动更新，也可以按下面顺序执行：

macOS：

```bash
cd ~/Documents/amazon-ops-toolbox
git pull --ff-only
bash scripts/setup-cn.sh
bash scripts/stop.sh
bash scripts/start.sh
```

Windows PowerShell：

```powershell
cd $HOME\Documents\amazon-ops-toolbox
git pull --ff-only
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-cn.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\stop.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

## 常见问题

### 页面打不开

先确认服务是否启动：

```bash
curl http://127.0.0.1:8080/api/health
```

正常会返回：

```json
{
  "ok": true
}
```

如果打不开，查看日志：

macOS：

```bash
tail -n 80 data/logs/server.log
```

Windows PowerShell：

```powershell
Get-Content data\logs\server.err.log -Tail 80
Get-Content data\logs\server.out.log -Tail 80
```

### 启动日志出现 `ModuleNotFoundError: No module named 'cgi'`

这是 Python 3.13 移除了旧版 `cgi` 标准库导致的错误。当前项目代码已经移除了对 `cgi` 的依赖。如果仍然看到这个错误，说明服务器上还在运行旧代码或旧进程：

macOS：

```bash
git pull --ff-only
bash scripts/setup-cn.sh
bash scripts/stop.sh
bash scripts/start.sh
```

Windows PowerShell：

```powershell
git pull --ff-only
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-cn.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\stop.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

如果仍然失败，优先安装 Python 3.11 或 3.12 后删除 `.venv`，再重新运行 `setup-cn` 脚本。

### 同事电脑访问不了

检查这几项：

- 服务器电脑和同事电脑是否在同一个局域网。
- `config/app-config.json` 里的 `server.host` 是否是 `0.0.0.0`。
- macOS 或 Windows 防火墙是否允许访问 `8080` 端口。
- 同事访问的是 `http://服务器局域网IP:8080/`，不是 `127.0.0.1`。

### 登录失败

确认输入框里真的输入了用户名和密码。登录页不会预填真实账号密码。

默认初始化账号：

```text
用户名：admin
密码：admin123
```

如果部署时设置过 `AMAZON_TOOLBOX_ADMIN_PASSWORD`，就使用你设置的新密码。

### 扫描服务器文件夹失败

系统只允许扫描 `config/app-config.json` 里 `paths.allowed_input_roots` 配置的目录。把业务文件夹加入白名单后，重启服务：

macOS：

```bash
bash scripts/stop.sh
bash scripts/start.sh
```

Windows PowerShell：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\stop.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

### 更新后配置没有变化

这是正常现象。`config/app-config.json` 是本机私有配置，不跟随 GitHub 更新。如果 README 或 `config/app-config.example.json` 增加了新配置项，需要手动把需要的配置复制到自己的 `config/app-config.json`，再重启服务。

不要把开发者电脑里的路径原样复制到部署机器，例如 `/Users/xukeqiang/...` 只适用于开发者本机。部署机器应该写自己的路径，例如：

```json
"allowed_input_roots": [
  "/Users/Shared/EcommerceData"
]
```

Windows 示例：

```json
"allowed_input_roots": [
  "D:/Operations/Amazon"
]
```

### 更新脚本看起来没反应

先确认是在终端或 PowerShell 里运行脚本，不要双击脚本文件。双击可能一闪而过，看不到 GitHub 网络、Python 依赖或重启服务的输出。

如果部署机器上还是旧版更新脚本，先手动拉一次代码：

macOS：

```bash
cd ~/Documents/amazon-ops-toolbox
git pull --ff-only
bash scripts/update.sh
```

Windows PowerShell：

```powershell
cd $HOME\Documents\amazon-ops-toolbox
git pull --ff-only
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\update.ps1
```

新版更新脚本会显示项目目录、当前版本、远程仓库、拉取进度、依赖安装进度和服务重启结果。如果停在某一步，把终端里的文字或截图发给维护人员即可定位。

### 汇总报告 PDF 店铺名提醒是什么意思

汇总报告 PDF 会优先使用文件名或文件夹里的店铺名，方便按团队交付口径汇总。PDF 正文里的 `Display name` 更适合做核验来源。

如果文件名里是 `VINAEMO`，但 PDF 里识别到 `Keebofly`，首字母 `V` 和 `K` 不一致，系统会在继续处理前提醒。这通常表示文件放错目录、文件名处理错误，或 PDF 本身属于另一个店铺。确认无误可以继续；不确定时建议取消任务，先整理原始文件。

## 当前能力

- 批量读取亚马逊货件 PDF。
- 提取 `Single SKU`、SKU、产品名称、目的地国家、仓库、FBA 物流编码前 12 位、箱码个数。
- 从运营文件名中解析工厂名、SKU、产品名、总数、仓库、FBA 编码、国家。
- 将 PDF 内容与文件名中的 SKU、国家、仓库、FBA 编码、箱数/总数做一致性校验。
- 生成规范文件名预览，并在表格中标记具体告警项。
- 人工确认后按工厂生成 zip，并在每个工厂压缩包内继续按国家分文件夹。
- 支持汇总报告 PDF 批量提取并导出 Excel。
- 汇总报告 PDF 使用文件名/目录店铺名作为主店铺，并用 PDF Display name 做首字母核验提醒。
- 支持亚马逊交易明细 CSV/XLSX 批量上传、拖放、清洗、汇总和审计导出。
- 支持港杂费发票 PDF 批量提取，生成“发票汇总”和“费用明细”Excel 工作簿。
- 支持沃尔玛交易数据 Excel 批量上传、拖放、清洗合并，生成经营数据总表和清洗审计。
- 支持管理员/操作员登录；管理员可管理用户。
- 使用 SQLite 持久化历史任务、导出记录和操作日志。
- 支持 CSV、Excel、zip 等常用导出。

## 货件 PDF 命名规则

```text
工厂名-SKU-产品名-总数-仓库-FBA物流编码-国家.pdf
```

示例：

```text
鹏鑫达-1006702-瑞奇白-40-CLT2-FBA19D8ZT5XR-美国.pdf
```

其中工厂名只来自文件名，PDF 正文内不会强行推断。总数来自 PDF 中的每箱数量乘箱码/页数，并与文件名中的总数比对。

## 数据不要提交到 GitHub

这些内容会被 `.gitignore` 忽略：

- `data/`：运行数据、用户、SQLite、上传文件、导出文件、备份。
- `config/app-config.json`：服务器本机配置。
- PDF、CSV、Excel、zip 等业务文件。

部署新机器时，从 GitHub 拉代码，然后按上面的步骤重新创建配置和运行数据。

## 更多部署说明

更详细的内网部署说明见：

```text
docs/lan-deployment.md
```
