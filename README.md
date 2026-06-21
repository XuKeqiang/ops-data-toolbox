# Amazon Operations Toolbox

内部亚马逊经营数据工具箱。当前阶段实现货件外箱标 PDF 的批量识别、文件名核验、导出、按工厂打包，以及交易报告 PDF 的结构化提取；后续可扩展交易明细 CSV、持久化历史任务和更多导入导出能力。

## 当前能力

- 批量读取亚马逊货件 PDF。
- 提取 `Single SKU`、SKU、产品名称、目的地国家、仓库、FBA 物流编码前 12 位、箱码个数。
- 从运营文件名中解析工厂名、SKU、产品名、总数、仓库、FBA 编码、国家。
- 将 PDF 内容与文件名中的 SKU、国家、仓库、FBA 编码、箱数/总数做一致性校验。
- 生成规范文件名预览，并在表格中标记具体告警项。
- 人工确认后按工厂把原始 PDF 分别打包为 zip。
- 导出 CSV 和 Excel。
- 在浏览器中确认后执行重命名。
- 支持上传 PDF 或扫描项目目录内的服务器文件夹。
- 支持管理员/操作员登录；管理员可管理用户。
- 支持交易报告 PDF 批量提取并导出 Excel。

## 安装依赖

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## 启动 Web 工具

```bash
/Users/xukeqiang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m app.amazon_toolbox.server --host 0.0.0.0 --port 8080
```

本机访问：

```text
http://127.0.0.1:8080/
```

公司内网访问时，把服务器 IP 给同事：

```text
http://<server-ip>:8080/
```

## 命令行扫描

```bash
/Users/xukeqiang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m app.amazon_toolbox.cli scan-shipments 20260619 --csv data/outputs/20260619.csv --xlsx data/outputs/20260619.xlsx
```

## 货件 PDF 命名规则

```text
工厂名-SKU-产品名-总数-仓库-FBA物流编码-国家.pdf
```

示例：

```text
鹏鑫达-1006702-瑞奇白-40-CLT2-FBA19D8ZT5XR-美国.pdf
```

其中工厂名只来自文件名，PDF 正文内不会强行推断。总数来自 PDF 中的每箱数量乘箱码/页数，并与文件名中的总数比对。

## GitHub 管理建议

首次托管时：

```bash
git init
git add .
git commit -m "feat: add amazon operations toolbox mvp"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

运行数据目录 `data/`、PDF、CSV、Excel、zip 已被 `.gitignore` 忽略，避免把团队上传的业务文件、导出文件或用户数据提交到 GitHub。

## 服务器部署建议

第一阶段可以直接在公司机器上运行 Python 服务。建议目录结构：

```text
Amazon_Data_Management/
  app/
  docs/
  tests/
  data/
    uploads/
    outputs/
```

后续增强：

- 用 SQLite 保存历史任务、操作者、导出记录和重命名日志。
- 加 Dockerfile，把启动命令固化成容器服务。
- 加反向代理和公司内网访问控制。
- 为 `transaction_pdf`、`transaction_csv` 增加独立解析模块，复用当前批次结果和导出界面。
