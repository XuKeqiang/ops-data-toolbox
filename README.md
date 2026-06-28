# Amazon Operations Toolbox

内部亚马逊经营数据工具箱。当前阶段支持货件外箱标 PDF 识别与规范命名、交易报告 PDF 提取、交易明细 CSV/XLSX 汇总清洗、导出下载、用户权限、历史任务持久化和内网部署。

## 适合谁看

- 只想把系统部署到公司电脑上的同事：看“零基础部署步骤”。
- 日常使用系统的运营同事：看“怎么打开和使用”。
- 负责后续维护代码的人：看“日常更新代码”和 `docs/lan-deployment.md`。

## 零基础部署步骤

下面以 macOS 公司电脑为例。目标是：这台电脑作为服务器，其他同事通过局域网浏览器访问。

### 1. 准备一台服务器电脑

建议：

- 电脑长期在线，不要经常关机。
- 连接公司内网。
- 最好给这台电脑固定局域网 IP。

### 2. 安装基础软件

打开“终端”应用，先检查是否已经安装 Git 和 Python：

```bash
git --version
python3 --version
```

如果提示找不到 `git` 或 `python3`：

- Git：可以安装 Xcode Command Line Tools，终端里执行 `xcode-select --install`。
- Python：建议安装 Python 3.11 或 3.12。

### 3. 拉取项目代码

选择一个固定目录存放项目，例如 `Documents`：

```bash
cd ~/Documents
git clone https://github.com/XuKeqiang/amazon-ops-toolbox.git
cd amazon-ops-toolbox
```

以后所有操作都在这个 `amazon-ops-toolbox` 文件夹里执行。

### 4. 安装 Python 依赖

第一次部署需要创建虚拟环境并安装依赖：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

如果安装过程没有报错，就可以进入下一步。

### 5. 创建配置文件

复制一份配置模板：

```bash
cp config/app-config.example.json config/app-config.json
```

打开 `config/app-config.json`，重点检查：

- `server.host`：内网部署建议保持 `0.0.0.0`。
- `server.port`：默认 `8080`，端口冲突时再改。
- `paths.allowed_input_roots`：允许系统扫描的服务器文件夹白名单。
- `limits.max_upload_mb`：单次上传大小限制。

如果不确定怎么改，先保持默认配置也可以启动。

### 6. 设置管理员初始密码

第一次启动前，建议设置一个正式管理员密码：

```bash
export AMAZON_TOOLBOX_ADMIN_PASSWORD='换成你的强密码'
```

如果没有设置，默认管理员账号是：

```text
用户名：admin
密码：admin123
```

部署给团队使用前，建议登录后立刻在“设置”里修改或新建正式管理员账号。

### 7. 启动服务

```bash
bash scripts/start.sh
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

```bash
ipconfig getifaddr en0
```

如果这条命令没有输出，可以到 macOS “系统设置 → 网络”里查看当前网络的 IP 地址。

### 8. 停止服务

```bash
bash scripts/stop.sh
```

### 9. 设置开机自启动和每日备份

确认系统能正常打开后，再执行：

```bash
bash scripts/install-launchd.sh
```

安装后：

- 电脑登录后会自动启动服务。
- 每天 02:30 自动备份一次。
- 备份文件在 `data/backups/`。

也可以手动备份：

```bash
bash scripts/backup.sh
```

## 怎么打开和使用

1. 打开浏览器访问 `http://服务器电脑的局域网IP:8080/`。
2. 管理员登录后，可以在“设置”里新增操作员账号。
3. 操作员登录后，可以处理自己权限范围内的数据任务。
4. 货件 PDF 支持上传一批 PDF、拖放文件夹，或扫描服务器白名单目录。
5. 识别结果表格支持搜索、筛选、排序和导出。
6. 交易报告 PDF、交易明细 CSV/XLSX 可以在对应模块里输入服务器文件夹路径后处理。
7. 历史任务会保存到 SQLite，服务重启后仍可查看。

## 日常更新代码

当 GitHub 仓库有新版本时，在服务器电脑执行：

```bash
cd ~/Documents/amazon-ops-toolbox
bash scripts/update.sh
```

它会自动：

- 拉取最新代码
- 更新 Python 依赖
- 停止旧服务
- 启动新服务

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

```bash
tail -n 80 data/logs/server.log
```

### 同事电脑访问不了

检查这几项：

- 服务器电脑和同事电脑是否在同一个局域网。
- `config/app-config.json` 里的 `server.host` 是否是 `0.0.0.0`。
- macOS 防火墙是否允许访问 `8080` 端口。
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

```bash
bash scripts/stop.sh
bash scripts/start.sh
```

## 当前能力

- 批量读取亚马逊货件 PDF。
- 提取 `Single SKU`、SKU、产品名称、目的地国家、仓库、FBA 物流编码前 12 位、箱码个数。
- 从运营文件名中解析工厂名、SKU、产品名、总数、仓库、FBA 编码、国家。
- 将 PDF 内容与文件名中的 SKU、国家、仓库、FBA 编码、箱数/总数做一致性校验。
- 生成规范文件名预览，并在表格中标记具体告警项。
- 人工确认后按工厂把原始 PDF 分别打包为 zip。
- 支持交易报告 PDF 批量提取并导出 Excel。
- 支持交易明细 CSV/XLSX 批量清洗、汇总和审计导出。
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
