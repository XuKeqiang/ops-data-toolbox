#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

step() {
  echo
  echo "==> $1"
}

fail_hint() {
  echo
  echo "更新没有完成。请把上面的报错截图发给维护人员。"
  echo "常见原因：没有进入项目目录、GitHub 网络不可达、本地文件被手动改动、Python 环境安装失败。"
}
trap fail_hint ERR

echo "Amazon Operations Toolbox 更新开始"
echo "项目目录：$ROOT_DIR"

if ! command -v git >/dev/null 2>&1; then
  echo "未找到 git。请先安装 Git，然后重新运行本脚本。"
  exit 1
fi

if [[ ! -d ".git" ]]; then
  echo "当前文件夹不是 Git 仓库。请先从 GitHub 拉取项目，或进入 amazon-ops-toolbox 项目目录后再运行。"
  exit 1
fi

CURRENT_BRANCH="$(git branch --show-current || true)"
CURRENT_COMMIT="$(git rev-parse --short HEAD)"
REMOTE_URL="$(git remote get-url origin 2>/dev/null || echo "未配置 origin")"

echo "当前分支：${CURRENT_BRANCH:-未知}"
echo "当前版本：$CURRENT_COMMIT"
echo "远程仓库：$REMOTE_URL"

if [[ -n "$(git status --short)" ]]; then
  echo
  echo "检测到本地有未提交改动，暂不自动拉取，避免覆盖部署机器上的本地修改："
  git status --short
  echo
  echo "如果这些改动只是误改，请先备份或联系维护人员处理。"
  exit 1
fi

step "拉取 GitHub 最新代码"
git fetch --prune --progress origin
git pull --ff-only --progress

UPDATED_COMMIT="$(git rev-parse --short HEAD)"
if [[ "$UPDATED_COMMIT" == "$CURRENT_COMMIT" ]]; then
  echo "代码已经是最新版本：$UPDATED_COMMIT"
else
  echo "代码已更新：$CURRENT_COMMIT -> $UPDATED_COMMIT"
fi

step "检查并更新 Python 依赖"
bash scripts/setup-cn.sh

step "重启服务"
bash scripts/stop.sh
bash scripts/start.sh

trap - ERR
echo
echo "更新完成。请刷新浏览器页面后重新使用系统。"
