#!/usr/bin/env bash
# 电商经营数据工具箱 — macOS 一键安装 / 更新脚本
# ============================================================
# 用途：任何人（无需技术背景）双击本文件即可：
#   1) 清理之前部署遗留的旧进程 / 旧开机任务 / 旧 App 入口
#   2) 从 GitHub 拉取最新代码
#   3) 准备 Python 运行环境（首次会联网安装依赖）
#   4) 在「启动台 / 应用程序」里生成「电商经营数据工具箱」App（双击即打开软件）
#   5) 设置开机自动启动，并立即启动服务
# 本脚本可重复运行（幂等），既可用于首次安装，也可用于日后更新。
# ============================================================
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$ROOT_DIR/data/logs"
APP_DEST="$HOME/Applications"
APP_NAME="电商经营数据工具箱"
LABEL="com.ecom.ops-toolbox.server"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
PORT="8080"
UID_VAL="$(id -u)"

mkdir -p "$LOG_DIR" "$APP_DEST"

log(){ echo "[$(date '+%H:%M:%S')] $*"; }
step(){ echo; echo "========== $* =========="; }

# 选择兼容的 Python（需 3.11 / 3.12；本项目用了 cgi 模块，3.13 已移除）
pick_python(){
  for cand in "${PYTHON:-}" /opt/anaconda3/bin/python3 /usr/local/bin/python3.12 \
              /usr/local/bin/python3.11 /usr/bin/python3.11 /usr/bin/python3.12 /usr/bin/python3; do
    [ -x "$cand" ] || continue
    local ver
    ver="$("$cand" -c "import sys;print('%d.%d'%sys.version_info[:2])" 2>/dev/null)" || continue
    local maj="${ver%.*}" min="${ver#*.}"
    if [ "$maj" -eq 3 ] && { [ "$min" -eq 11 ] || [ "$min" -eq 12 ]; }; then
      echo "$cand"; return 0
    fi
  done
  return 1
}

step "0/5 消除之前部署的影响"
# 停止所有相关服务进程（旧模块名 + 新模块名，防止端口被旧实例占用）
pkill -f "app.amazon_toolbox.server" 2>/dev/null && log "已停止旧模块名进程" || true
pkill -f "app.ops_toolbox.server" 2>/dev/null && log "已停止旧服务实例" || true
sleep 1
# 卸载并删除任何引用本项目的 launchd 开机任务（无论标签叫什么）
for p in "$HOME"/Library/LaunchAgents/*.plist; do
  [ -e "$p" ] || continue
  if grep -q "$ROOT_DIR" "$p" 2>/dev/null; then
    launchctl bootout "gui/$UID_VAL/$(defaults read "$p" Label 2>/dev/null)" 2>/dev/null || true
    launchctl unload "$p" 2>/dev/null || true
    rm -f "$p"
    log "已清理旧开机任务: $(basename "$p")"
  fi
done
# 删除旧的 Amazon 品牌 App 入口（仓库根 / 应用程序 / 桌面）
for base in "$ROOT_DIR" "$APP_DEST" "$HOME/Desktop"; do
  for d in "$base"/Amazon\ 经营工具箱*.app; do
    [ -e "$d" ] && rm -rf "$d" && log "已删除旧 App 入口: $d" || true
  done
done
# 检查旧环境变量痕迹（仅提示，不修改用户 shell 配置）
if grep -rIl "AMAZON_TOOLBOX" "$HOME/.zshrc" "$HOME/.bash_profile" "$HOME/.profile" "$HOME/.zprofile" 2>/dev/null | grep -q .; then
  log "提示：检测到 shell 配置里仍有 AMAZON_TOOLBOX_* 旧环境变量。新版本不再读取它，可保留也可手动删除，不影响使用。"
fi

step "1/5 拉取最新代码"
cd "$ROOT_DIR"
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
  git diff > "$LOG_DIR/pre-update-$(date '+%Y%m%d-%H%M%S').patch" 2>/dev/null || true
  log "已把本地改动备份到 data/logs/（部署机通常无需本地改动）"
fi
git fetch origin
git reset --hard origin/main
log "代码已更新到 $(git rev-parse --short HEAD)"

step "2/5 准备 Python 运行环境"
if ! PY="$(pick_python)"; then
  log "错误：未找到 Python 3.11 / 3.12。请先安装其中之一后再运行本脚本。"
  if [ -t 0 ]; then read -n1 -r -p "按任意键关闭..."; fi
  exit 1
fi
log "使用 Python: $PY ($("$PY" -c 'import sys;print(sys.version.split()[0])'))"
# 若已有 .venv 但 Python 版本不兼容（如 3.13），则删掉重建
if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
  VMINOR="$("$ROOT_DIR/.venv/bin/python" -c 'import sys;print(sys.version_info.minor)' 2>/dev/null)"
  if [ "$VMINOR" != "11" ] && [ "$VMINOR" != "12" ]; then
    log "检测到 .venv 由不兼容的 Python $VMINOR 构建，重建中..."
    rm -rf "$ROOT_DIR/.venv"
  fi
fi
if [ ! -x "$ROOT_DIR/.venv/bin/python" ]; then
  log "首次安装依赖（使用清华镜像，可能需要几分钟，请耐心等待）..."
  PY="$PY" bash "$ROOT_DIR/scripts/setup-cn.sh"
else
  "$ROOT_DIR/.venv/bin/python" -m pip install -q -r "$ROOT_DIR/requirements.txt" 2>&1 | tail -3
  log "依赖已就绪"
fi

step "3/5 生成系统 App 入口（启动台 / 应用程序）"
make_app(){
  local name="$1" mode="$2"
  local app="$APP_DEST/$name.app"
  rm -rf "$app"
  mkdir -p "$app/Contents/MacOS"
  cat > "$app/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>$name</string>
  <key>CFBundleDisplayName</key><string>$name</string>
  <key>CFBundleExecutable</key><string>launcher</string>
  <key>CFBundleIdentifier</key><string>$LABEL</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleVersion</key><string>1.0</string>
</dict>
</plist>
PLIST
  if [ "$mode" = "open" ]; then
    cat > "$app/Contents/MacOS/launcher" <<'LAUNCH'
#!/usr/bin/env bash
LABEL="com.ecom.ops-toolbox.server"
PORT="8080"
PROJECT_DIR="__ROOT_DIR__"
launchctl kickstart "gui/$(id -u)/$LABEL" 2>/dev/null || bash "$PROJECT_DIR/scripts/start.sh" >/dev/null 2>&1
READY=0
for i in $(seq 1 20); do
  if (exec 3<>"/dev/tcp/127.0.0.1/$PORT") 2>/dev/null; then
    exec 3>&- 2>/dev/null; READY=1; break
  fi
  sleep 0.5
done
if [ "$READY" -eq 1 ]; then
  /usr/bin/open "http://127.0.0.1:$PORT/"
  /usr/bin/osascript -e 'display notification "已打开 电商经营数据工具箱" with title "电商经营数据工具箱" sound name "Glass"'
else
  /usr/bin/osascript -e 'display notification "服务未就绪，请双击“更新”脚本或重启电脑" with title "电商经营数据工具箱" sound name "Basso"'
fi
LAUNCH
  else
    cat > "$app/Contents/MacOS/launcher" <<'LAUNCH'
#!/usr/bin/env bash
LABEL="com.ecom.ops-toolbox.server"
PROJECT_DIR="__ROOT_DIR__"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
pkill -f "app.ops_toolbox.server" 2>/dev/null || true
/usr/bin/osascript -e 'display notification "服务已停止" with title "电商经营数据工具箱" sound name "Glass"'
LAUNCH
  fi
  sed -i '' "s|__ROOT_DIR__|$ROOT_DIR|" "$app/Contents/MacOS/launcher"
  chmod +x "$app/Contents/MacOS/launcher"
  xattr -dr com.apple.quarantine "$app" 2>/dev/null || true
  log "已生成: $app"
}
make_app "$APP_NAME" open
make_app "$APP_NAME-停止" stop
# 同时放一份到项目目录，方便找回
rm -rf "$ROOT_DIR/$APP_NAME.app" "$ROOT_DIR/$APP_NAME-停止.app"
cp -R "$APP_DEST/$APP_NAME.app" "$ROOT_DIR/" 2>/dev/null || true
cp -R "$APP_DEST/$APP_NAME-停止.app" "$ROOT_DIR/" 2>/dev/null || true
# 把本更新脚本也放进应用程序，方便日后双击更新
cp "$SCRIPT_DIR/$(basename "$0")" "$APP_DEST/" 2>/dev/null || true
xattr -dr com.apple.quarantine "$APP_DEST/$(basename "$0")" 2>/dev/null || true

step "4/5 安装开机自动启动（launchd）"
cat > "$PLIST" <<LPLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$ROOT_DIR/scripts/run-server.sh</string>
  </array>
  <key>WorkingDirectory</key><string>$ROOT_DIR</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>EnvironmentVariables</key>
  <dict>
    <key>OPS_TOOLBOX_HOST</key><string>0.0.0.0</string>
    <key>PATH</key><string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
  <key>StandardOutPath</key><string>$LOG_DIR/launchd.out.log</string>
  <key>StandardErrorPath</key><string>$LOG_DIR/launchd.err.log</string>
</dict>
</plist>
LPLIST
LAUNCHD_OK=0
if launchctl bootstrap "gui/$UID_VAL" "$PLIST" 2>/dev/null; then
  launchctl kickstart "gui/$UID_VAL/$LABEL" 2>/dev/null || true
  LAUNCHD_OK=1
  log "已加载开机自启任务（登录后自动运行，崩溃会自动重启）"
else
  log "提示：当前环境（非图形登录会话）无法加载 launchd，已改由后台进程方式启动；在您的 Mac 登录后会正常自启。"
fi

step "5/5 启动服务并验证"
if [ "$LAUNCHD_OK" -eq 0 ]; then
  bash "$ROOT_DIR/scripts/start.sh" >/dev/null 2>&1 || true
fi
READY=0
for i in $(seq 1 40); do
  if (exec 3<>"/dev/tcp/127.0.0.1/$PORT") 2>/dev/null; then
    exec 3>&- 2>/dev/null; READY=1; break
  fi
  sleep 0.5
done
if [ "$READY" -eq 1 ]; then
  log "服务已在 http://127.0.0.1:$PORT/ 运行"
  LOCAL_IP="$(ipconfig getifaddr en0 2>/dev/null)"
  if [ -n "$LOCAL_IP" ]; then
    log "同事可通过本机局域网地址访问：http://$LOCAL_IP:$PORT/"
  fi
else
  log "服务端口暂未就绪。请查看："
  log "  - $LOG_DIR/server.log"
  log "  - $LOG_DIR/launchd.err.log"
fi

echo
log "全部完成！以后操作非常简单："
log "  • 打开软件：双击「启动台 / 应用程序」里的「$APP_NAME」"
log "  • 更新代码：双击「启动台 / 应用程序」里的「$(basename "$0")」"
log "  • 停止服务：双击「$APP_NAME-停止」"
log "  （本机已设置开机自动启动，无需每次手动开。）"

if [ -t 0 ]; then
  echo; read -n1 -r -p "按任意键关闭窗口..."
fi
