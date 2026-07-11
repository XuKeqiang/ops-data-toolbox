#!/usr/bin/env python3
"""Detached updater launched by the authenticated web administration page."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "data" / "web-update-status.json"


def update_command(platform_name: str | None = None) -> list[str]:
    platform_name = platform_name or os.name
    if platform_name == "nt":
        return [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            r".\scripts\update.ps1",
        ]
    return ["bash", "scripts/update.sh"]


def write_status(token: str, phase: str, message: str) -> None:
    payload = {
        "token": token,
        "phase": phase,
        "message": message,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    temp_path = STATUS_PATH.with_suffix(".tmp")
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
    temp_path.replace(STATUS_PATH)


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    token = sys.argv[1]
    time.sleep(2)
    write_status(token, "running", "正在拉取远端代码并更新依赖")
    try:
        result = subprocess.run(
            update_command(),
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=900,
        )
    except subprocess.TimeoutExpired:
        write_status(token, "failed", "更新超时，请联系维护人员查看 data/logs/web-update.log")
        return 1
    print(result.stdout, flush=True)
    if result.returncode != 0:
        write_status(token, "failed", "更新未完成，本地数据未被删除，请查看更新日志")
        return result.returncode
    write_status(token, "completed", "更新已完成，服务已重启，请重新登录")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
