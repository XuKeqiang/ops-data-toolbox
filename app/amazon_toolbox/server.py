from __future__ import annotations

import argparse
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="cgi")

import cgi
import json
import mimetypes
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

from .auth import (
    ensure_user_store,
    find_user_by_id,
    find_user_by_username,
    hash_password,
    load_users,
    normalize_username,
    public_user,
    save_users,
    validate_role,
    verify_password,
)
from .report_pdf.batch import ReportPdfJob, process_report_folder
from .shipment_pdf.batch import (
    apply_renames,
    export_csv,
    export_xlsx,
    package_by_factory,
    plan_renames,
    scan_folder,
)
from .shipment_pdf.models import ShipmentRecord


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = APP_ROOT / "static"
DATA_ROOT = PROJECT_ROOT / "data"
UPLOAD_ROOT = DATA_ROOT / "uploads"
OUTPUT_ROOT = DATA_ROOT / "outputs"
USER_STORE = DATA_ROOT / "users.json"
LEGACY_REPORT_ROOT = Path("/Users/xukeqiang/Documents/Amazon_Data_Process")
ALLOWED_INPUT_ROOTS = (PROJECT_ROOT.resolve(), LEGACY_REPORT_ROOT.resolve())


@dataclass
class BatchState:
    batch_id: str
    source_label: str
    records: list[ShipmentRecord]
    created_at: str
    owner_id: str
    owner_name: str


BATCHES: dict[str, BatchState] = {}
REPORT_JOBS: dict[str, ReportPdfJob] = {}
TASK_HISTORY: list[dict] = []
SESSIONS: dict[str, str] = {}
SHIPMENT_PACKAGES: dict[str, list[dict]] = {}


class AmazonToolboxHandler(BaseHTTPRequestHandler):
    server_version = "AmazonToolbox/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_file(STATIC_ROOT / "index.html")
        elif parsed.path.startswith("/static/"):
            self._send_file(STATIC_ROOT / parsed.path.removeprefix("/static/"))
        elif parsed.path == "/api/health":
            self._send_json({"ok": True})
        elif parsed.path == "/api/session":
            self._handle_session()
        elif parsed.path == "/api/history":
            self._handle_history()
        elif parsed.path == "/api/settings":
            self._handle_settings()
        elif parsed.path == "/api/users":
            self._handle_users()
        elif parsed.path == "/api/export":
            self._handle_export(parse_qs(parsed.query))
        elif parsed.path == "/api/report-pdf/download":
            self._handle_report_download(parse_qs(parsed.query))
        elif parsed.path == "/api/shipment-package/download":
            self._handle_shipment_package_download(parse_qs(parsed.query))
        else:
            self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/scan-folder":
            self._handle_scan_folder()
        elif parsed.path == "/api/login":
            self._handle_login()
        elif parsed.path == "/api/logout":
            self._handle_logout()
        elif parsed.path == "/api/users":
            self._handle_create_user()
        elif parsed.path == "/api/report-pdf/process-folder":
            self._handle_report_process_folder()
        elif parsed.path == "/api/upload":
            self._handle_upload()
        elif parsed.path == "/api/rename":
            self._handle_rename()
        elif parsed.path == "/api/package-by-factory":
            self._handle_package_by_factory()
        else:
            self._send_json({"error": "Not found"}, status=404)

    def do_PATCH(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/users/"):
            self._handle_update_user(parsed.path.removeprefix("/api/users/"))
        else:
            self._send_json({"error": "Not found"}, status=404)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/users/"):
            self._handle_delete_user(parsed.path.removeprefix("/api/users/"))
        else:
            self._send_json({"error": "Not found"}, status=404)

    def log_message(self, format: str, *args) -> None:
        print(f"{self.address_string()} - {format % args}")

    def _handle_session(self) -> None:
        user = self._current_user()
        self._send_json({"authenticated": bool(user), "user": public_user(user)})

    def _handle_login(self) -> None:
        payload = self._read_json()
        username = normalize_username(str(payload.get("username", "")))
        password = str(payload.get("password", ""))
        users = load_users(USER_STORE)
        user = find_user_by_username(users, username)
        if not user or not user.get("active", True) or not verify_password(password, user.get("password_hash", "")):
            self._send_json({"error": "账号或密码不正确"}, status=401)
            return

        token = uuid.uuid4().hex + uuid.uuid4().hex
        SESSIONS[token] = user["id"]
        self._send_json(
            {"authenticated": True, "user": public_user(user)},
            headers={"Set-Cookie": _session_cookie(token)},
        )

    def _handle_logout(self) -> None:
        token = self._session_token()
        if token:
            SESSIONS.pop(token, None)
        self._send_json({"ok": True}, headers={"Set-Cookie": _clear_session_cookie()})

    def _handle_history(self) -> None:
        user = self._require_auth()
        if not user:
            return
        self._send_json(_history_payload(user))

    def _handle_settings(self) -> None:
        user = self._require_auth()
        if not user:
            return
        self._send_json(_settings_payload(self.server.server_address, user))

    def _handle_users(self) -> None:
        user = self._require_admin()
        if not user:
            return
        self._send_json({"users": [public_user(item) for item in load_users(USER_STORE)]})

    def _handle_create_user(self) -> None:
        admin = self._require_admin()
        if not admin:
            return
        payload = self._read_json()
        username = normalize_username(str(payload.get("username", "")))
        password = str(payload.get("password", ""))
        display_name = str(payload.get("display_name", "")).strip() or username
        role = validate_role(str(payload.get("role", "operator")))

        if len(username) < 3:
            self._send_json({"error": "用户名至少需要 3 个字符"}, status=400)
            return
        if len(password) < 6:
            self._send_json({"error": "密码至少需要 6 个字符"}, status=400)
            return

        users = load_users(USER_STORE)
        if find_user_by_username(users, username):
            self._send_json({"error": "用户名已存在"}, status=400)
            return

        now = _now_label()
        new_user = {
            "id": uuid.uuid4().hex,
            "username": username,
            "display_name": display_name,
            "role": role,
            "active": bool(payload.get("active", True)),
            "password_hash": hash_password(password),
            "created_at": now,
            "updated_at": now,
        }
        users.append(new_user)
        save_users(USER_STORE, users)
        self._send_json({"user": public_user(new_user)})

    def _handle_update_user(self, user_id: str) -> None:
        admin = self._require_admin()
        if not admin:
            return
        payload = self._read_json()
        users = load_users(USER_STORE)
        user = find_user_by_id(users, user_id)
        if not user:
            self._send_json({"error": "用户不存在"}, status=404)
            return

        if "display_name" in payload:
            user["display_name"] = str(payload.get("display_name", "")).strip() or user["username"]
        if "role" in payload:
            next_role = validate_role(str(payload.get("role", user["role"])))
            if user["id"] == admin["id"] and next_role != user["role"]:
                self._send_json({"error": "不能修改当前登录管理员的角色"}, status=400)
                return
            if user.get("role") == "admin" and next_role != "admin" and _active_admin_count(users) <= 1:
                self._send_json({"error": "至少需要保留一个启用的管理员"}, status=400)
                return
            user["role"] = next_role
        if "active" in payload:
            if user["id"] == admin["id"] and not bool(payload.get("active")):
                self._send_json({"error": "不能停用当前登录的管理员"}, status=400)
                return
            if user.get("role") == "admin" and user.get("active", True) and not bool(payload.get("active")):
                if _active_admin_count(users) <= 1:
                    self._send_json({"error": "至少需要保留一个启用的管理员"}, status=400)
                    return
            user["active"] = bool(payload.get("active"))
        if payload.get("password"):
            password = str(payload.get("password"))
            if len(password) < 6:
                self._send_json({"error": "密码至少需要 6 个字符"}, status=400)
                return
            user["password_hash"] = hash_password(password)
        user["updated_at"] = _now_label()
        save_users(USER_STORE, users)
        self._send_json({"user": public_user(user)})

    def _handle_delete_user(self, user_id: str) -> None:
        admin = self._require_admin()
        if not admin:
            return
        if user_id == admin["id"]:
            self._send_json({"error": "不能删除当前登录的管理员"}, status=400)
            return
        users = load_users(USER_STORE)
        user = find_user_by_id(users, user_id)
        if not user:
            self._send_json({"error": "用户不存在"}, status=404)
            return
        users = [item for item in users if item["id"] != user_id]
        save_users(USER_STORE, users)
        for token, session_user_id in list(SESSIONS.items()):
            if session_user_id == user_id:
                SESSIONS.pop(token, None)
        self._send_json({"deleted": True})

    def _handle_scan_folder(self) -> None:
        user = self._require_auth()
        if not user:
            return
        payload = self._read_json()
        folder_text = str(payload.get("folder", "")).strip()
        if not folder_text:
            self._send_json({"error": "请提供服务器上的文件夹路径"}, status=400)
            return

        folder = _resolve_allowed_folder(folder_text)
        if folder is None:
            self._send_json({"error": f"为了安全，当前只允许扫描这些目录：{_allowed_roots_label()}"}, status=400)
            return
        if not folder.exists() or not folder.is_dir():
            self._send_json({"error": "文件夹不存在或不是有效目录"}, status=400)
            return

        records = scan_folder(folder)
        batch = _store_batch(source_label=str(folder), records=records, owner=user)
        self._send_json(_batch_payload(batch))

    def _handle_report_process_folder(self) -> None:
        user = self._require_auth()
        if not user:
            return
        payload = self._read_json()
        folder_text = str(payload.get("folder", "")).strip()
        if not folder_text:
            self._send_json({"error": "请提供服务器上的交易报告 PDF 文件夹路径"}, status=400)
            return

        folder = _resolve_allowed_folder(folder_text)
        if folder is None:
            self._send_json({"error": f"为了安全，当前只允许扫描这些目录：{_allowed_roots_label()}"}, status=400)
            return
        if not folder.exists() or not folder.is_dir():
            self._send_json({"error": "文件夹不存在或不是有效目录"}, status=400)
            return

        job_id = _new_batch_id()
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_ROOT / f"{job_id}-amazon-report-pdf-results.xlsx"
        job = process_report_folder(folder, output_path, job_id)
        REPORT_JOBS[job.job_id] = job
        _record_history(
            task_id=job.job_id,
            task_type="report_pdf",
            title="交易报告 PDF",
            source_label=job.source_label,
            summary=job.summary,
            status="需复核" if job.summary.get("warnings") else "完成",
            downloads=[{"label": "Excel 工作簿", "url": f"/api/report-pdf/download?job_id={job.job_id}"}],
            owner=user,
        )
        self._send_json(_report_job_payload(job))

    def _handle_upload(self) -> None:
        user = self._require_auth()
        if not user:
            return
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self._send_json({"error": "请上传 multipart/form-data 文件"}, status=400)
            return

        batch_id = _new_batch_id()
        upload_dir = UPLOAD_ROOT / batch_id
        upload_dir.mkdir(parents=True, exist_ok=True)

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
                "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
            },
        )

        saved = 0
        files = form["files"] if "files" in form else []
        if not isinstance(files, list):
            files = [files]
        for item in files:
            if not getattr(item, "filename", ""):
                continue
            filename = Path(item.filename).name
            if not filename.lower().endswith(".pdf"):
                continue
            target = upload_dir / filename
            with target.open("wb") as handle:
                shutil.copyfileobj(item.file, handle)
            saved += 1

        if saved == 0:
            shutil.rmtree(upload_dir, ignore_errors=True)
            self._send_json({"error": "没有收到 PDF 文件"}, status=400)
            return

        records = scan_folder(upload_dir)
        batch = _store_batch(source_label=f"上传批次 {batch_id}", records=records, batch_id=batch_id, owner=user)
        self._send_json(_batch_payload(batch))

    def _handle_export(self, query: dict[str, list[str]]) -> None:
        user = self._require_auth()
        if not user:
            return
        batch_id = _first_query(query, "batch_id")
        export_format = _first_query(query, "format") or "csv"
        batch = BATCHES.get(batch_id)
        if not batch:
            self._send_json({"error": "批次不存在或服务已重启"}, status=404)
            return
        if not _can_access_owner(user, batch.owner_id):
            self._send_json({"error": "没有权限导出该批次"}, status=403)
            return

        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        if export_format == "xlsx":
            output_path = OUTPUT_ROOT / f"{batch.batch_id}-shipment-results.xlsx"
            export_xlsx(batch.records, output_path)
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            output_path = OUTPUT_ROOT / f"{batch.batch_id}-shipment-results.csv"
            export_csv(batch.records, output_path)
            content_type = "text/csv; charset=utf-8"

        self._send_download(output_path, content_type)

    def _handle_report_download(self, query: dict[str, list[str]]) -> None:
        user = self._require_auth()
        if not user:
            return
        job_id = _first_query(query, "job_id")
        job = REPORT_JOBS.get(job_id)
        if not job:
            self._send_json({"error": "任务不存在或服务已重启"}, status=404)
            return
        history_item = next((item for item in TASK_HISTORY if item["id"] == job_id), None)
        if history_item and not _can_access_owner(user, history_item.get("owner_id", "")):
            self._send_json({"error": "没有权限下载该任务"}, status=403)
            return
        self._send_download(
            job.output_path,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def _handle_shipment_package_download(self, query: dict[str, list[str]]) -> None:
        user = self._require_auth()
        if not user:
            return
        batch_id = _first_query(query, "batch_id")
        filename = Path(_first_query(query, "filename")).name
        batch = BATCHES.get(batch_id)
        if not batch:
            self._send_json({"error": "批次不存在或服务已重启"}, status=404)
            return
        if not _can_access_owner(user, batch.owner_id):
            self._send_json({"error": "没有权限下载该批次"}, status=403)
            return
        package = next((item for item in SHIPMENT_PACKAGES.get(batch_id, []) if item.get("zip_filename") == filename), None)
        if not package:
            self._send_json({"error": "打包文件不存在"}, status=404)
            return
        zip_path = Path(package["zip_path"])
        if not zip_path.exists():
            self._send_json({"error": "打包文件已被移动或删除"}, status=404)
            return
        self._send_download(zip_path, "application/zip")

    def _handle_rename(self) -> None:
        user = self._require_auth()
        if not user:
            return
        payload = self._read_json()
        batch_id = str(payload.get("batch_id", ""))
        confirm = bool(payload.get("confirm", False))
        batch = BATCHES.get(batch_id)
        if not batch:
            self._send_json({"error": "批次不存在或服务已重启"}, status=404)
            return
        if not _can_access_owner(user, batch.owner_id):
            self._send_json({"error": "没有权限重命名该批次"}, status=403)
            return
        if not confirm:
            self._send_json({"error": "重命名需要 confirm=true"}, status=400)
            return

        plans = apply_renames(batch.records)
        self._send_json(
            {
                "batch_id": batch.batch_id,
                "renamed": sum(1 for plan in plans if plan.can_apply),
                "plans": [plan.as_dict() for plan in plans],
            }
        )

    def _handle_package_by_factory(self) -> None:
        user = self._require_auth()
        if not user:
            return
        payload = self._read_json()
        batch_id = str(payload.get("batch_id", ""))
        confirm = bool(payload.get("confirm", False))
        batch = BATCHES.get(batch_id)
        if not batch:
            self._send_json({"error": "批次不存在或服务已重启"}, status=404)
            return
        if not _can_access_owner(user, batch.owner_id):
            self._send_json({"error": "没有权限打包该批次"}, status=403)
            return
        if not confirm:
            self._send_json({"error": "按工厂打包需要 confirm=true"}, status=400)
            return

        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        result = package_by_factory(batch.records, OUTPUT_ROOT, batch.batch_id)
        packages = [
            {
                **package,
                "download_url": (
                    f"/api/shipment-package/download?batch_id={batch.batch_id}"
                    f"&filename={quote(package['zip_filename'])}"
                ),
            }
            for package in result["packages"]
        ]
        SHIPMENT_PACKAGES[batch.batch_id] = packages
        _update_history_downloads(
            batch.batch_id,
            [{"label": f"{item['factory_name']} 压缩包", "url": item["download_url"]} for item in packages],
        )
        self._send_json(
            {
                "batch_id": batch.batch_id,
                "package_root": result["package_root"],
                "packages": packages,
                "skipped": result["skipped"],
            }
        )

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def _send_json(self, payload: dict, status: int = 200, headers: dict[str, str] | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _current_user(self) -> dict | None:
        token = self._session_token()
        if not token:
            return None
        user_id = SESSIONS.get(token)
        if not user_id:
            return None
        user = find_user_by_id(load_users(USER_STORE), user_id)
        if not user or not user.get("active", True):
            SESSIONS.pop(token, None)
            return None
        return user

    def _require_auth(self) -> dict | None:
        user = self._current_user()
        if not user:
            self._send_json({"error": "请先登录"}, status=401)
            return None
        return user

    def _require_admin(self) -> dict | None:
        user = self._require_auth()
        if not user:
            return None
        if user.get("role") != "admin":
            self._send_json({"error": "需要管理员权限"}, status=403)
            return None
        return user

    def _session_token(self) -> str:
        cookie = self.headers.get("Cookie", "")
        for part in cookie.split(";"):
            key, _, value = part.strip().partition("=")
            if key == "amazon_toolbox_session":
                return value
        return ""

    def _send_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self._send_json({"error": "Not found"}, status=404)
            return
        content = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_download(self, path: Path, content_type: str) -> None:
        content = path.read_bytes()
        fallback_name = _ascii_download_filename(path.name)
        encoded_name = quote(path.name)
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header(
            "Content-Disposition",
            f"attachment; filename=\"{fallback_name}\"; filename*=UTF-8''{encoded_name}",
        )
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def _store_batch(
    source_label: str, records: list[ShipmentRecord], owner: dict, batch_id: str | None = None
) -> BatchState:
    batch_id = batch_id or _new_batch_id()
    created_at = _now_label()
    batch = BatchState(
        batch_id=batch_id,
        source_label=source_label,
        records=records,
        created_at=created_at,
        owner_id=owner["id"],
        owner_name=owner.get("display_name") or owner["username"],
    )
    BATCHES[batch_id] = batch
    valid_count = sum(1 for record in records if record.is_valid)
    needs_review = len(records) - valid_count
    _record_history(
        task_id=batch_id,
        task_type="shipment_pdf",
        title="货件 PDF",
        source_label=source_label,
        summary={
            "files": len(records),
            "boxes": sum(record.box_count for record in records),
            "valid": valid_count,
            "needs_review": needs_review,
        },
        status="需复核" if needs_review else "完成",
        downloads=[
            {"label": "CSV 文件", "url": f"/api/export?batch_id={batch_id}&format=csv"},
            {"label": "Excel 工作簿", "url": f"/api/export?batch_id={batch_id}&format=xlsx"},
        ],
        owner=owner,
    )
    return batch


def _batch_payload(batch: BatchState) -> dict:
    plans = plan_renames(batch.records)
    valid_count = sum(1 for record in batch.records if record.is_valid)
    return {
        "batch_id": batch.batch_id,
        "source_label": batch.source_label,
        "summary": {
            "files": len(batch.records),
            "boxes": sum(record.box_count for record in batch.records),
            "valid": valid_count,
            "needs_review": len(batch.records) - valid_count,
        },
        "records": [
            {
                **record.as_dict(),
                "suggested_filename": plan.target_path.name,
                "rename": plan.as_dict(),
            }
            for record, plan in zip(batch.records, plans)
        ],
    }


def _report_job_payload(job: ReportPdfJob) -> dict:
    return {
        "job_id": job.job_id,
        "source_label": job.source_label,
        "summary": job.summary,
        "rows": job.rows,
        "download_url": f"/api/report-pdf/download?job_id={job.job_id}",
    }


def _history_payload(user: dict) -> dict:
    tasks = TASK_HISTORY if user.get("role") == "admin" else [
        task for task in TASK_HISTORY if task.get("owner_id") == user["id"]
    ]
    return {
        "tasks": list(reversed(tasks)),
        "summary": {
            "total": len(tasks),
            "shipment_pdf": sum(1 for task in tasks if task["type"] == "shipment_pdf"),
            "report_pdf": sum(1 for task in tasks if task["type"] == "report_pdf"),
            "needs_review": sum(1 for task in tasks if task["status"] == "需复核"),
        },
    }


def _settings_payload(server_address: tuple[str, int], user: dict) -> dict:
    host, port = server_address
    return {
        "current_user": public_user(user),
        "permissions": {
            "can_process_files": True,
            "can_manage_users": user.get("role") == "admin",
            "history_scope": "全部任务" if user.get("role") == "admin" else "仅本人任务",
        },
        "service": {
            "name": "Amazon 经营工具箱",
            "address": f"http://{host}:{port}/",
            "status": "运行中",
        },
        "paths": {
            "project_root": str(PROJECT_ROOT.resolve()),
            "output_root": str(OUTPUT_ROOT.resolve()),
            "upload_root": str(UPLOAD_ROOT.resolve()),
            "allowed_input_roots": [str(root) for root in ALLOWED_INPUT_ROOTS if root.exists()],
        },
        "processing": [
            {"name": "货件 PDF", "engine": "pdfplumber / pypdf 规则提取", "llm": "不依赖"},
            {"name": "交易报告 PDF", "engine": "pdfplumber 表格结构解析 + 对账校验", "llm": "不依赖"},
        ],
        "exports": ["CSV", "Excel"],
        "deployment_notes": [
            "当前服务可部署在公司内网机器上，由团队通过浏览器访问。",
            "上传文件写入 data/uploads，导出文件写入 data/outputs。",
            "历史任务当前保存在服务运行内存中，重启后会清空；后续可升级为 SQLite 或 JSON 持久化。",
        ],
    }


def _record_history(
    task_id: str,
    task_type: str,
    title: str,
    source_label: str,
    summary: dict,
    status: str,
    downloads: list[dict],
    owner: dict,
) -> None:
    TASK_HISTORY.append(
        {
            "id": task_id,
            "type": task_type,
            "title": title,
            "source_label": source_label,
            "created_at": _now_label(),
            "summary": summary,
            "status": status,
            "downloads": downloads,
            "owner_id": owner["id"],
            "owner_name": owner.get("display_name") or owner["username"],
            "owner_username": owner["username"],
        }
    )
    del TASK_HISTORY[:-80]


def _update_history_downloads(task_id: str, downloads: list[dict]) -> None:
    for task in TASK_HISTORY:
        if task["id"] != task_id:
            continue
        existing_urls = {item.get("url") for item in task.get("downloads", [])}
        task.setdefault("downloads", []).extend(
            item for item in downloads if item.get("url") not in existing_urls
        )
        break


def _resolve_allowed_folder(folder_text: str) -> Path | None:
    folder = Path(folder_text).expanduser().resolve()
    for root in ALLOWED_INPUT_ROOTS:
        try:
            folder.relative_to(root)
            return folder
        except ValueError:
            continue
    return None


def _allowed_roots_label() -> str:
    return "、".join(str(root) for root in ALLOWED_INPUT_ROOTS if root.exists())


def _new_batch_id() -> str:
    return uuid.uuid4().hex[:12]


def _can_access_owner(user: dict, owner_id: str) -> bool:
    return user.get("role") == "admin" or user.get("id") == owner_id


def _active_admin_count(users: list[dict]) -> int:
    return sum(1 for user in users if user.get("role") == "admin" and user.get("active", True))


def _session_cookie(token: str) -> str:
    return f"amazon_toolbox_session={token}; Path=/; HttpOnly; SameSite=Lax"


def _clear_session_cookie() -> str:
    return "amazon_toolbox_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"


def _now_label() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _first_query(query: dict[str, list[str]], key: str) -> str:
    values = query.get(key, [])
    return values[0] if values else ""


def _ascii_download_filename(filename: str) -> str:
    cleaned = "".join(char if 32 <= ord(char) < 127 and char not in {'"', "\\"} else "_" for char in filename)
    return cleaned or "download"


def run(host: str, port: int) -> None:
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    ensure_user_store(USER_STORE)
    server = ThreadingHTTPServer((host, port), AmazonToolboxHandler)
    print(f"Amazon Operations Toolbox running at http://{host}:{port}/")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Amazon Operations Toolbox")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()
