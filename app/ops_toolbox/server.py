from __future__ import annotations

import argparse
import json
import mimetypes
import shutil
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime
from email.parser import BytesParser
from email.policy import default as email_default_policy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

from .auth import (
    ensure_user_store,
    find_user_by_id,
    find_user_by_username,
    hash_password,
    load_users,
    normalize_password,
    normalize_username,
    public_user,
    save_users,
    validate_role,
    verify_password,
)
from .config import APP_ROOT, DEFAULT_INPUT_ROOT, PROJECT_ROOT, STATIC_ROOT, load_config
from .port_fee_pdf.batch import PortFeePdfJob, process_port_fee_folder
from .report_pdf.batch import ReportPdfJob, preflight_report_folder, process_report_folder
from .shipment_pdf.batch import (
    apply_renames,
    export_csv,
    export_xlsx,
    package_by_factory,
    plan_renames,
    scan_folder,
)
from .shipment_pdf.models import ShipmentRecord
from .storage import (
    delete_task,
    get_task,
    init_db,
    list_tasks,
    prune_tasks,
    record_export,
    record_operation,
    record_task,
    update_task_downloads,
)
from .transaction_csv.batch import TransactionCsvJob, process_transaction_folder
from .walmart_transaction.batch import WalmartTransactionJob, process_walmart_transaction_folder


CONFIG = load_config()
DATA_ROOT = CONFIG.data_root
UPLOAD_ROOT = CONFIG.upload_root
OUTPUT_ROOT = CONFIG.output_root
USER_STORE = CONFIG.user_store
DATABASE_PATH = CONFIG.database_path
ALLOWED_INPUT_ROOTS = CONFIG.allowed_input_roots


@dataclass
class BatchState:
    batch_id: str
    source_label: str
    records: list[ShipmentRecord]
    created_at: str
    owner_id: str
    owner_name: str


@dataclass
class UploadedFile:
    filename: str
    content: bytes


BATCHES: dict[str, BatchState] = {}
REPORT_JOBS: dict[str, ReportPdfJob] = {}
TRANSACTION_JOBS: dict[str, TransactionCsvJob] = {}
WALMART_TRANSACTION_JOBS: dict[str, WalmartTransactionJob] = {}
PORT_FEE_JOBS: dict[str, PortFeePdfJob] = {}
SESSIONS: dict[str, str] = {}
REPORT_PREFLIGHTS: dict[str, Path] = {}
SHIPMENT_PACKAGES: dict[str, list[dict]] = {}
SHIPMENT_PACKAGE_BUNDLES: dict[str, dict] = {}
SHIPMENT_SELECTED_PACKAGES: dict[str, list[dict]] = {}


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
        elif parsed.path == "/api/transaction-csv/download":
            self._handle_transaction_download(parse_qs(parsed.query))
        elif parsed.path == "/api/walmart-transaction/download":
            self._handle_walmart_transaction_download(parse_qs(parsed.query))
        elif parsed.path == "/api/port-fee-pdf/download":
            self._handle_port_fee_download(parse_qs(parsed.query))
        elif parsed.path == "/api/shipment-package/download":
            self._handle_shipment_package_download(parse_qs(parsed.query))
        elif parsed.path == "/api/shipment-package/download-all":
            self._handle_shipment_package_download_all(parse_qs(parsed.query))
        elif parsed.path == "/api/shipment-selection/download":
            self._handle_shipment_selection_download(parse_qs(parsed.query))
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
        elif parsed.path == "/api/report-pdf/preflight-folder":
            self._handle_report_preflight_folder()
        elif parsed.path == "/api/report-pdf/preflight-upload":
            self._handle_report_preflight_upload()
        elif parsed.path == "/api/report-pdf/process-preflight-upload":
            self._handle_report_process_preflight_upload()
        elif parsed.path == "/api/report-pdf/process-folder":
            self._handle_report_process_folder()
        elif parsed.path == "/api/report-pdf/upload":
            self._handle_report_upload()
        elif parsed.path == "/api/transaction-csv/process-folder":
            self._handle_transaction_process_folder()
        elif parsed.path == "/api/transaction-csv/upload":
            self._handle_transaction_upload()
        elif parsed.path == "/api/walmart-transaction/process-folder":
            self._handle_walmart_transaction_process_folder()
        elif parsed.path == "/api/walmart-transaction/upload":
            self._handle_walmart_transaction_upload()
        elif parsed.path == "/api/port-fee-pdf/process-folder":
            self._handle_port_fee_process_folder()
        elif parsed.path == "/api/port-fee-pdf/upload":
            self._handle_port_fee_upload()
        elif parsed.path == "/api/upload":
            self._handle_upload()
        elif parsed.path == "/api/rename":
            self._handle_rename()
        elif parsed.path == "/api/package-by-factory":
            self._handle_package_by_factory()
        elif parsed.path == "/api/shipment-selection/package":
            self._handle_shipment_selection_package()
        elif parsed.path == "/api/history/cleanup":
            self._handle_history_cleanup()
        elif parsed.path == "/api/history/batch-delete":
            self._handle_history_batch_delete()
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
        elif parsed.path.startswith("/api/history/"):
            self._handle_history_delete(parsed.path.removeprefix("/api/history/"))
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
        password = normalize_password(str(payload.get("password", "")))
        users = load_users(USER_STORE)
        user = find_user_by_username(users, username)
        if not user or not user.get("active", True) or not verify_password(password, user.get("password_hash", "")):
            self._send_json({"error": "账号或密码不正确"}, status=401)
            return

        token = uuid.uuid4().hex + uuid.uuid4().hex
        SESSIONS[token] = user["id"]
        record_operation(
            DATABASE_PATH,
            operation="login",
            owner=user,
            target_id=user["id"],
            target_type="user",
            message="用户登录",
        )
        self._send_json(
            {"authenticated": True, "user": public_user(user)},
            headers={"Set-Cookie": _session_cookie(token)},
        )

    def _handle_logout(self) -> None:
        user = self._current_user()
        token = self._session_token()
        if token:
            SESSIONS.pop(token, None)
        if user:
            record_operation(
                DATABASE_PATH,
                operation="logout",
                owner=user,
                target_id=user["id"],
                target_type="user",
                message="用户退出登录",
            )
        self._send_json({"ok": True}, headers={"Set-Cookie": _clear_session_cookie()})

    def _handle_history(self) -> None:
        user = self._require_auth()
        if not user:
            return
        self._send_json(_history_payload(user))

    def _handle_history_delete(self, task_id: str) -> None:
        user = self._require_auth()
        if not user:
            return
        task = get_task(DATABASE_PATH, task_id)
        if not task:
            self._send_json({"error": "历史任务不存在"}, status=404)
            return
        if not _can_access_owner(user, task.get("owner_id", "")):
            self._send_json({"error": "没有权限删除该历史任务"}, status=403)
            return
        removed_files = _remove_task_artifacts(task)
        deleted = delete_task(DATABASE_PATH, task_id)
        record_operation(
            DATABASE_PATH,
            operation="history_delete",
            owner=user,
            target_id=task_id,
            target_type=task.get("type", ""),
            message=f"删除历史任务：{task.get('title', task_id)}",
            payload={"deleted": deleted, "removed_files": removed_files},
        )
        self._send_json({"deleted": deleted, "removed_files": removed_files})

    def _handle_history_cleanup(self) -> None:
        user = self._require_admin()
        if not user:
            return
        payload = self._read_json()
        days = int(payload.get("days", 30) or 30)
        if days < 1:
            self._send_json({"error": "保留天数至少为 1 天"}, status=400)
            return
        tasks = prune_tasks(DATABASE_PATH, user, days)
        removed_files = sum(_remove_task_artifacts(task) for task in tasks)
        record_operation(
            DATABASE_PATH,
            operation="history_cleanup",
            owner=user,
            target_type="history",
            message=f"清理 {days} 天前历史任务",
            payload={"days": days, "deleted": len(tasks), "removed_files": removed_files},
        )
        self._send_json({"deleted": len(tasks), "removed_files": removed_files, "days": days})

    def _handle_history_batch_delete(self) -> None:
        user = self._require_auth()
        if not user:
            return
        payload = self._read_json()
        task_ids = [str(item) for item in payload.get("task_ids", []) if str(item)]
        if not task_ids:
            self._send_json({"error": "请选择要删除的历史任务"}, status=400)
            return
        deleted = 0
        removed_files = 0
        skipped: list[str] = []
        for task_id in task_ids:
            task = get_task(DATABASE_PATH, task_id)
            if not task or not _can_access_owner(user, task.get("owner_id", "")):
                skipped.append(task_id)
                continue
            removed_files += _remove_task_artifacts(task)
            if delete_task(DATABASE_PATH, task_id):
                deleted += 1
        record_operation(
            DATABASE_PATH,
            operation="history_batch_delete",
            owner=user,
            target_type="history",
            message=f"批量删除历史任务：{deleted} 条",
            payload={"requested": len(task_ids), "deleted": deleted, "skipped": skipped, "removed_files": removed_files},
        )
        self._send_json({"deleted": deleted, "skipped": skipped, "removed_files": removed_files})

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
        record_operation(
            DATABASE_PATH,
            operation="user_create",
            owner=admin,
            target_id=new_user["id"],
            target_type="user",
            message=f"创建用户 {new_user['username']}",
            payload={"role": role, "active": new_user["active"]},
        )
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
        record_operation(
            DATABASE_PATH,
            operation="user_update",
            owner=admin,
            target_id=user["id"],
            target_type="user",
            message=f"更新用户 {user['username']}",
            payload={"fields": sorted(payload.keys())},
        )
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
        record_operation(
            DATABASE_PATH,
            operation="user_delete",
            owner=admin,
            target_id=user_id,
            target_type="user",
            message=f"删除用户 {user['username']}",
        )
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
        record_operation(
            DATABASE_PATH,
            operation="shipment_scan_folder",
            owner=user,
            target_id=batch.batch_id,
            target_type="shipment_pdf",
            message=f"扫描货件 PDF 文件夹：{folder}",
            payload={"records": len(records)},
        )
        logs = [
            {"level": "info", "message": f"开始扫描服务器文件夹：{folder}"},
            {"level": "success", "message": f"扫描完成：识别到 {len(records)} 个 PDF"},
        ]
        self._send_json(_batch_payload(batch, logs=logs))

    def _handle_report_preflight_folder(self) -> None:
        user = self._require_auth()
        if not user:
            return
        payload = self._read_json()
        folder_text = str(payload.get("folder", "")).strip()
        if not folder_text:
            self._send_json({"error": "请提供服务器上的汇总报告 PDF 文件夹路径"}, status=400)
            return
        folder = _resolve_allowed_folder(folder_text)
        if folder is None:
            self._send_json({"error": f"为了安全，当前只允许扫描这些目录：{_allowed_roots_label()}"}, status=400)
            return
        if not folder.exists() or not folder.is_dir():
            self._send_json({"error": "文件夹不存在或不是有效目录"}, status=400)
            return
        preflight = preflight_report_folder(folder)
        self._send_json({"source_label": str(folder), **preflight})

    def _handle_report_preflight_upload(self) -> None:
        user = self._require_auth()
        if not user:
            return
        saved = self._save_report_upload_for_preflight()
        if "error" in saved:
            self._send_json(saved, status=saved.get("status", 400))
            return
        upload_dir = Path(saved["upload_dir"])
        preflight = preflight_report_folder(upload_dir)
        REPORT_PREFLIGHTS[saved["preflight_id"]] = upload_dir
        self._send_json({
            "preflight_id": saved["preflight_id"],
            "source_label": f"上传预检 {saved['preflight_id']}",
            "received": saved["received"],
            "saved": saved["saved"],
            "skipped": saved["skipped"],
            "skipped_paths": saved["skipped_paths"],
            "renamed": saved["renamed"],
            **preflight,
        })

    def _handle_report_process_preflight_upload(self) -> None:
        user = self._require_auth()
        if not user:
            return
        payload = self._read_json()
        preflight_id = str(payload.get("preflight_id", "")).strip()
        upload_dir = REPORT_PREFLIGHTS.pop(preflight_id, None)
        if not upload_dir or not upload_dir.exists():
            self._send_json({"error": "预检批次不存在或已处理，请重新上传"}, status=404)
            return
        self._process_report_folder_for_user(upload_dir, user, source_label=f"上传批次 {preflight_id}", job_id=preflight_id)

    def _handle_report_process_folder(self) -> None:
        user = self._require_auth()
        if not user:
            return
        payload = self._read_json()
        folder_text = str(payload.get("folder", "")).strip()
        if not folder_text:
            self._send_json({"error": "请提供服务器上的汇总报告 PDF 文件夹路径"}, status=400)
            return

        folder = _resolve_allowed_folder(folder_text)
        if folder is None:
            self._send_json({"error": f"为了安全，当前只允许扫描这些目录：{_allowed_roots_label()}"}, status=400)
            return
        if not folder.exists() or not folder.is_dir():
            self._send_json({"error": "文件夹不存在或不是有效目录"}, status=400)
            return

        self._process_report_folder_for_user(folder, user)

    def _process_report_folder_for_user(self, folder: Path, user: dict, source_label: str | None = None, job_id: str | None = None) -> None:
        job_id = job_id or _new_batch_id()
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_ROOT / f"{job_id}-amazon-report-pdf-results.xlsx"
        job = process_report_folder(folder, output_path, job_id)
        if source_label:
            job.source_label = source_label
        REPORT_JOBS[job.job_id] = job
        _record_history(
            task_id=job.job_id,
            task_type="report_pdf",
            title="汇总报告 PDF",
            source_label=job.source_label,
            summary=job.summary,
            status="需复核" if job.summary.get("warnings") else "完成",
            downloads=[{"label": "Excel 工作簿", "url": f"/api/report-pdf/download?job_id={job.job_id}"}],
            owner=user,
        )
        record_operation(
            DATABASE_PATH,
            operation="report_pdf_process_folder",
            owner=user,
            target_id=job.job_id,
            target_type="report_pdf",
            message=f"处理汇总报告 PDF 文件夹：{folder}",
            payload=job.summary,
        )
        self._send_json(_report_job_payload(job))

    def _read_multipart_files(self, content_type: str, content_length: int) -> list[UploadedFile]:
        body = self.rfile.read(content_length)
        header = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
        message = BytesParser(policy=email_default_policy).parsebytes(header + body)
        if not message.is_multipart():
            return []
        files: list[UploadedFile] = []
        for part in message.iter_parts():
            disposition = part.get_content_disposition()
            field_name = part.get_param("name", header="content-disposition")
            filename = part.get_filename()
            if disposition != "form-data" or field_name != "files" or not filename:
                continue
            files.append(UploadedFile(filename=filename, content=part.get_payload(decode=True) or b""))
        return files

    def _save_uploaded_files(self, upload_dir: Path, allowed_suffixes: set[str], empty_error: str) -> dict:
        content_length = int(self.headers.get("Content-Length", "0") or "0")
        if content_length > CONFIG.max_upload_bytes:
            return {
                "error": f"上传内容超过限制：当前上限 {CONFIG.max_upload_mb} MB",
                "status": 413,
            }
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            return {"error": "请上传 multipart/form-data 文件", "status": 400}

        upload_dir.mkdir(parents=True, exist_ok=True)
        files = self._read_multipart_files(content_type, content_length)

        received = saved = skipped = renamed = 0
        skipped_paths: list[str] = []
        for item in files:
            received += 1
            upload_path = _safe_upload_relative_path(item.filename)
            if upload_path is None or upload_path.suffix.lower() not in allowed_suffixes:
                skipped += 1
                skipped_paths.append(_upload_display_path(item.filename))
                continue
            target = _unique_upload_target(upload_dir / upload_path)
            if target.name != upload_path.name or target.parent != upload_dir / upload_path.parent:
                renamed += 1
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(item.content)
            saved += 1

        if saved == 0:
            shutil.rmtree(upload_dir, ignore_errors=True)
            return {
                "error": empty_error,
                "received": received,
                "saved": saved,
                "skipped": skipped,
                "skipped_paths": skipped_paths,
                "status": 400,
            }

        return {
            "received": received,
            "saved": saved,
            "skipped": skipped,
            "skipped_paths": skipped_paths,
            "renamed": renamed,
        }

    def _save_report_upload_for_preflight(self) -> dict:
        preflight_id = _new_batch_id()
        upload_dir = UPLOAD_ROOT / f"{preflight_id}-report-pdf"
        saved_upload = self._save_uploaded_files(upload_dir, {".pdf"}, "没有收到 PDF 文件")
        if "error" in saved_upload:
            return saved_upload
        return {
            "preflight_id": preflight_id,
            "upload_dir": str(upload_dir),
            **saved_upload,
        }

    def _handle_report_upload(self) -> None:
        user = self._require_auth()
        if not user:
            return

        job_id = _new_batch_id()
        upload_dir = UPLOAD_ROOT / f"{job_id}-report-pdf"
        saved_upload = self._save_uploaded_files(upload_dir, {".pdf"}, "没有收到 PDF 文件")
        if "error" in saved_upload:
            self._send_json(saved_upload, status=saved_upload.get("status", 400))
            return

        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_ROOT / f"{job_id}-amazon-report-pdf-results.xlsx"
        job = process_report_folder(upload_dir, output_path, job_id)
        job.source_label = f"上传批次 {job_id}"
        job.summary.update(saved_upload)
        REPORT_JOBS[job.job_id] = job
        _record_history(
            task_id=job.job_id,
            task_type="report_pdf",
            title="汇总报告 PDF",
            source_label=f"上传批次 {job_id}",
            summary=job.summary,
            status="需复核" if job.summary.get("warnings") else "完成",
            downloads=[{"label": "Excel 工作簿", "url": f"/api/report-pdf/download?job_id={job.job_id}"}],
            owner=user,
        )
        record_operation(
            DATABASE_PATH,
            operation="report_pdf_upload",
            owner=user,
            target_id=job.job_id,
            target_type="report_pdf",
            message=f"上传并处理汇总报告 PDF：{job_id}",
            payload=job.summary,
        )
        self._send_json(_report_job_payload(job))

    def _handle_transaction_process_folder(self) -> None:
        user = self._require_auth()
        if not user:
            return
        payload = self._read_json()
        folder_text = str(payload.get("folder", "")).strip()
        if not folder_text:
            self._send_json({"error": "请提供服务器上的交易明细 CSV/XLSX 文件夹路径"}, status=400)
            return

        folder = _resolve_allowed_folder(folder_text)
        if folder is None:
            self._send_json({"error": f"为了安全，当前只允许扫描这些目录：{_allowed_roots_label()}"}, status=400)
            return
        if not folder.exists() or not folder.is_dir():
            self._send_json({"error": "文件夹不存在或不是有效目录"}, status=400)
            return

        job_id = _new_batch_id()
        output_dir = OUTPUT_ROOT / f"{job_id}-transaction-csv"
        job = process_transaction_folder(
            folder,
            output_dir,
            job_id,
            label=folder.name,
            include_country_files=bool(payload.get("include_country_files", False)),
            include_quarter_backup=bool(payload.get("include_quarter_backup", False)),
        )
        TRANSACTION_JOBS[job.job_id] = job
        status = "需复核" if (
            job.summary.get("date_parse_failures")
            or job.summary.get("amount_failures")
            or job.summary.get("unresolved_country_files")
            or job.summary.get("unsupported_files")
        ) else "完成"
        _record_history(
            task_id=job.job_id,
            task_type="transaction_csv",
            title="交易明细 CSV",
            source_label=job.source_label,
            summary=job.summary,
            status=status,
            downloads=[
                {"label": "交易总表", "url": f"/api/transaction-csv/download?job_id={job.job_id}&file=total"},
                {"label": "审计报告", "url": f"/api/transaction-csv/download?job_id={job.job_id}&file=audit"},
            ],
            owner=user,
        )
        record_operation(
            DATABASE_PATH,
            operation="transaction_csv_process_folder",
            owner=user,
            target_id=job.job_id,
            target_type="transaction_csv",
            message=f"处理交易明细文件夹：{folder}",
            payload=job.summary,
        )
        self._send_json(_transaction_job_payload(job))

    def _handle_transaction_upload(self) -> None:
        user = self._require_auth()
        if not user:
            return
        job_id = _new_batch_id()
        upload_dir = UPLOAD_ROOT / f"{job_id}-transaction-csv"
        saved = self._save_table_upload(
            upload_dir,
            allowed_suffixes={".csv", ".xlsx", ".xls"},
            empty_error="没有收到 CSV/XLSX 交易明细文件",
        )
        if "error" in saved:
            self._send_json(saved, status=saved.get("status", 400))
            return

        output_dir = OUTPUT_ROOT / f"{job_id}-transaction-csv"
        job = process_transaction_folder(upload_dir, output_dir, job_id, label=f"上传批次 {job_id}")
        TRANSACTION_JOBS[job.job_id] = job
        job.summary.update({
            "received": saved["received"],
            "saved": saved["saved"],
            "skipped": saved["skipped"],
            "skipped_paths": saved["skipped_paths"],
            "renamed": saved["renamed"],
        })
        status = "需复核" if (
            job.summary.get("date_parse_failures")
            or job.summary.get("amount_failures")
            or job.summary.get("unresolved_country_files")
            or job.summary.get("unsupported_files")
            or job.summary.get("skipped")
        ) else "完成"
        _record_history(
            task_id=job.job_id,
            task_type="transaction_csv",
            title="交易明细 CSV",
            source_label=job.source_label,
            summary=job.summary,
            status=status,
            downloads=[
                {"label": "交易总表", "url": f"/api/transaction-csv/download?job_id={job.job_id}&file=total"},
                {"label": "审计报告", "url": f"/api/transaction-csv/download?job_id={job.job_id}&file=audit"},
            ],
            owner=user,
        )
        record_operation(
            DATABASE_PATH,
            operation="transaction_csv_upload",
            owner=user,
            target_id=job.job_id,
            target_type="transaction_csv",
            message=f"上传并处理交易明细：{job_id}",
            payload=job.summary,
        )
        self._send_json(_transaction_job_payload(job))

    def _handle_walmart_transaction_process_folder(self) -> None:
        user = self._require_auth()
        if not user:
            return
        payload = self._read_json()
        folder_text = str(payload.get("folder", "")).strip()
        if not folder_text:
            self._send_json({"error": "请提供服务器上的沃尔玛财务报表文件夹路径"}, status=400)
            return

        folder = _resolve_allowed_folder(folder_text)
        if folder is None:
            self._send_json({"error": f"为了安全，当前只允许扫描这些目录：{_allowed_roots_label()}"}, status=400)
            return
        if not folder.exists() or not folder.is_dir():
            self._send_json({"error": "文件夹不存在或不是有效目录"}, status=400)
            return

        job_id = _new_batch_id()
        output_dir = OUTPUT_ROOT / f"{job_id}-walmart-transaction"
        job = process_walmart_transaction_folder(folder, output_dir, job_id, label=folder.name)
        WALMART_TRANSACTION_JOBS[job.job_id] = job
        status = "需复核" if job.summary.get("warnings") or job.summary.get("unmapped_values") else "完成"
        _record_history(
            task_id=job.job_id,
            task_type="walmart_transaction",
            title="沃尔玛交易数据",
            source_label=job.source_label,
            summary=job.summary,
            status=status,
            downloads=[
                {"label": "经营数据总表", "url": f"/api/walmart-transaction/download?job_id={job.job_id}&file=total"},
                {"label": "清洗审计", "url": f"/api/walmart-transaction/download?job_id={job.job_id}&file=audit"},
            ],
            owner=user,
        )
        record_operation(
            DATABASE_PATH,
            operation="walmart_transaction_process_folder",
            owner=user,
            target_id=job.job_id,
            target_type="walmart_transaction",
            message=f"处理沃尔玛财务报表文件夹：{folder}",
            payload=job.summary,
        )
        self._send_json(_walmart_transaction_job_payload(job))

    def _handle_walmart_transaction_upload(self) -> None:
        user = self._require_auth()
        if not user:
            return
        job_id = _new_batch_id()
        upload_dir = UPLOAD_ROOT / f"{job_id}-walmart-transaction"
        saved = self._save_table_upload(
            upload_dir,
            allowed_suffixes={".xlsx", ".xlsm"},
            empty_error="没有收到 XLSX/XLSM 沃尔玛财务报表",
        )
        if "error" in saved:
            self._send_json(saved, status=saved.get("status", 400))
            return

        output_dir = OUTPUT_ROOT / f"{job_id}-walmart-transaction"
        job = process_walmart_transaction_folder(upload_dir, output_dir, job_id, label=f"上传批次 {job_id}")
        WALMART_TRANSACTION_JOBS[job.job_id] = job
        job.summary.update({
            "received": saved["received"],
            "saved": saved["saved"],
            "skipped": saved["skipped"],
            "skipped_paths": saved["skipped_paths"],
            "renamed": saved["renamed"],
        })
        status = "需复核" if job.summary.get("warnings") or job.summary.get("unmapped_values") or job.summary.get("skipped") else "完成"
        _record_history(
            task_id=job.job_id,
            task_type="walmart_transaction",
            title="沃尔玛交易数据",
            source_label=job.source_label,
            summary=job.summary,
            status=status,
            downloads=[
                {"label": "经营数据总表", "url": f"/api/walmart-transaction/download?job_id={job.job_id}&file=total"},
                {"label": "清洗审计", "url": f"/api/walmart-transaction/download?job_id={job.job_id}&file=audit"},
            ],
            owner=user,
        )
        record_operation(
            DATABASE_PATH,
            operation="walmart_transaction_upload",
            owner=user,
            target_id=job.job_id,
            target_type="walmart_transaction",
            message=f"上传并处理沃尔玛财务报表：{job_id}",
            payload=job.summary,
        )
        self._send_json(_walmart_transaction_job_payload(job))

    def _handle_port_fee_process_folder(self) -> None:
        user = self._require_auth()
        if not user:
            return
        payload = self._read_json()
        folder_text = str(payload.get("folder", "")).strip()
        if not folder_text:
            self._send_json({"error": "请提供服务器上的港杂费发票 PDF 文件夹路径"}, status=400)
            return

        folder = _resolve_allowed_folder(folder_text)
        if folder is None:
            self._send_json({"error": f"为了安全，当前只允许扫描这些目录：{_allowed_roots_label()}"}, status=400)
            return
        if not folder.exists() or not folder.is_dir():
            self._send_json({"error": "文件夹不存在或不是有效目录"}, status=400)
            return

        self._process_port_fee_folder_for_user(folder, user)

    def _handle_port_fee_upload(self) -> None:
        user = self._require_auth()
        if not user:
            return

        job_id = _new_batch_id()
        upload_dir = UPLOAD_ROOT / f"{job_id}-port-fee-pdf"
        saved_upload = self._save_uploaded_files(upload_dir, {".pdf"}, "没有收到 PDF 文件")
        if "error" in saved_upload:
            self._send_json(saved_upload, status=saved_upload.get("status", 400))
            return

        self._process_port_fee_folder_for_user(
            upload_dir,
            user,
            source_label=f"上传批次 {job_id}",
            job_id=job_id,
            upload_summary=saved_upload,
        )

    def _process_port_fee_folder_for_user(
        self,
        folder: Path,
        user: dict,
        source_label: str | None = None,
        job_id: str | None = None,
        upload_summary: dict | None = None,
    ) -> None:
        job_id = job_id or _new_batch_id()
        output_dir = OUTPUT_ROOT / f"{job_id}-port-fee-pdf"
        job = process_port_fee_folder(folder, output_dir, job_id, label=source_label or folder.name)
        if source_label:
            job.source_label = source_label
        if upload_summary:
            job.summary.update(upload_summary)
        PORT_FEE_JOBS[job.job_id] = job
        status = "需复核" if job.summary.get("warnings") or job.summary.get("failed") else "完成"
        _record_history(
            task_id=job.job_id,
            task_type="port_fee_pdf",
            title="港杂费 PDF",
            source_label=job.source_label,
            summary=job.summary,
            status=status,
            downloads=[{"label": "Excel 工作簿", "url": f"/api/port-fee-pdf/download?job_id={job.job_id}"}],
            owner=user,
        )
        record_operation(
            DATABASE_PATH,
            operation="port_fee_pdf_process",
            owner=user,
            target_id=job.job_id,
            target_type="port_fee_pdf",
            message=f"处理港杂费发票 PDF：{job.source_label}",
            payload=job.summary,
        )
        self._send_json(_port_fee_job_payload(job))

    def _save_table_upload(self, upload_dir: Path, allowed_suffixes: set[str], empty_error: str) -> dict:
        return self._save_uploaded_files(upload_dir, allowed_suffixes, empty_error)

    def _handle_upload(self) -> None:
        user = self._require_auth()
        if not user:
            return

        batch_id = _new_batch_id()
        upload_dir = UPLOAD_ROOT / batch_id
        saved_upload = self._save_uploaded_files(upload_dir, {".pdf"}, "没有收到 PDF 文件")
        if "error" in saved_upload:
            self._send_json({
                "error": saved_upload["error"],
                "logs": [
                    {"level": "info", "message": f"收到 {saved_upload.get('received', 0)} 个上传文件"},
                    {"level": "warning", "message": f"跳过 {saved_upload.get('skipped', 0)} 个非 PDF 或无效文件"},
                    *_skipped_path_logs(saved_upload.get("skipped_paths", [])),
                ],
            }, status=saved_upload.get("status", 400))
            return

        records = scan_folder(upload_dir)
        batch = _store_batch(source_label=f"上传批次 {batch_id}", records=records, batch_id=batch_id, owner=user)
        record_operation(
            DATABASE_PATH,
            operation="shipment_upload",
            owner=user,
            target_id=batch.batch_id,
            target_type="shipment_pdf",
            message=f"上传并扫描货件 PDF：{batch_id}",
            payload={**saved_upload, "records": len(records)},
        )
        logs = [
            {"level": "info", "message": f"收到 {saved_upload['received']} 个上传文件"},
            {"level": "success", "message": f"保存 {saved_upload['saved']} 个 PDF 到上传批次 {batch_id}"},
        ]
        if saved_upload["skipped"]:
            logs.append({"level": "warning", "message": f"跳过 {saved_upload['skipped']} 个非 PDF 或无效文件"})
            logs.extend(_skipped_path_logs(saved_upload["skipped_paths"]))
        if saved_upload["renamed"]:
            logs.append({"level": "warning", "message": f"发现 {saved_upload['renamed']} 个重名 PDF，已自动加序号保存"})
        logs.append({"level": "success", "message": f"扫描完成：识别到 {len(records)} 个 PDF"})
        self._send_json(_batch_payload(batch, logs=logs))

    def _handle_export(self, query: dict[str, list[str]]) -> None:
        user = self._require_auth()
        if not user:
            return
        batch_id = _first_query(query, "batch_id")
        export_format = _first_query(query, "format") or "csv"
        batch = BATCHES.get(batch_id)
        if not batch:
            history_item = get_task(DATABASE_PATH, batch_id)
            if not history_item:
                self._send_json({"error": "批次不存在或服务已重启"}, status=404)
                return
            if not _can_access_owner(user, history_item.get("owner_id", "")):
                self._send_json({"error": "没有权限导出该批次"}, status=403)
                return
            suffix = "xlsx" if export_format == "xlsx" else "csv"
            output_path = OUTPUT_ROOT / f"{batch_id}-shipment-results.{suffix}"
            if not output_path.is_file():
                self._send_json({"error": "历史导出文件不存在，请重新处理该批次"}, status=404)
                return
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if suffix == "xlsx" else "text/csv; charset=utf-8"
            record_export(
                DATABASE_PATH,
                task_id=batch_id,
                export_type=f"shipment_{export_format}",
                file_path=output_path,
                owner=user,
            )
            self._send_download(output_path, content_type)
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

        record_export(
            DATABASE_PATH,
            task_id=batch.batch_id,
            export_type=f"shipment_{export_format}",
            file_path=output_path,
            owner=user,
        )
        record_operation(
            DATABASE_PATH,
            operation="shipment_export",
            owner=user,
            target_id=batch.batch_id,
            target_type="shipment_pdf",
            message=f"导出货件识别结果：{output_path.name}",
            payload={"format": export_format},
        )
        self._send_download(output_path, content_type)

    def _handle_report_download(self, query: dict[str, list[str]]) -> None:
        user = self._require_auth()
        if not user:
            return
        job_id = _first_query(query, "job_id")
        job = REPORT_JOBS.get(job_id)
        history_item = get_task(DATABASE_PATH, job_id)
        if history_item and not _can_access_owner(user, history_item.get("owner_id", "")):
            self._send_json({"error": "没有权限下载该任务"}, status=403)
            return
        output_path = job.output_path if job else OUTPUT_ROOT / f"{job_id}-amazon-report-pdf-results.xlsx"
        if not output_path.is_file():
            self._send_json({"error": "导出文件不存在，请重新处理该任务"}, status=404)
            return
        record_export(
            DATABASE_PATH,
            task_id=job_id,
            export_type="report_pdf_xlsx",
            file_path=output_path,
            owner=user,
        )
        self._send_download(output_path, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    def _handle_transaction_download(self, query: dict[str, list[str]]) -> None:
        user = self._require_auth()
        if not user:
            return
        job_id = _first_query(query, "job_id")
        file_key = _first_query(query, "file") or "total"
        job = TRANSACTION_JOBS.get(job_id)
        history_item = get_task(DATABASE_PATH, job_id)
        if history_item and not _can_access_owner(user, history_item.get("owner_id", "")):
            self._send_json({"error": "没有权限下载该任务"}, status=403)
            return
        if job:
            path = job.audit_xlsx_path if file_key == "audit" else job.total_path
        else:
            filename_key = "audit_filename" if file_key == "audit" else "output_filename"
            filename = (history_item or {}).get("summary", {}).get(filename_key, "")
            path = OUTPUT_ROOT / f"{job_id}-transaction-csv" / filename
        if not path.is_file():
            self._send_json({"error": "导出文件不存在，请重新处理该任务"}, status=404)
            return
        record_export(
            DATABASE_PATH,
            task_id=job_id,
            export_type=f"transaction_csv_{file_key}",
            file_path=path,
            owner=user,
        )
        self._send_download(path, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    def _handle_walmart_transaction_download(self, query: dict[str, list[str]]) -> None:
        user = self._require_auth()
        if not user:
            return
        job_id = _first_query(query, "job_id")
        file_key = _first_query(query, "file") or "total"
        job = WALMART_TRANSACTION_JOBS.get(job_id)
        history_item = get_task(DATABASE_PATH, job_id)
        if history_item and not _can_access_owner(user, history_item.get("owner_id", "")):
            self._send_json({"error": "没有权限下载该任务"}, status=403)
            return
        if job:
            path = job.audit_path if file_key == "audit" else job.total_path
        else:
            filename_key = "audit_filename" if file_key == "audit" else "output_filename"
            filename = (history_item or {}).get("summary", {}).get(filename_key, "")
            path = OUTPUT_ROOT / f"{job_id}-walmart-transaction" / filename
        if not path.is_file():
            self._send_json({"error": "导出文件不存在，请重新处理该任务"}, status=404)
            return
        record_export(
            DATABASE_PATH,
            task_id=job_id,
            export_type=f"walmart_transaction_{file_key}",
            file_path=path,
            owner=user,
        )
        self._send_download(path, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    def _handle_port_fee_download(self, query: dict[str, list[str]]) -> None:
        user = self._require_auth()
        if not user:
            return
        job_id = _first_query(query, "job_id")
        job = PORT_FEE_JOBS.get(job_id)
        history_item = get_task(DATABASE_PATH, job_id)
        if history_item and not _can_access_owner(user, history_item.get("owner_id", "")):
            self._send_json({"error": "没有权限下载该任务"}, status=403)
            return
        if job:
            output_path = job.output_path
        else:
            filename = (history_item or {}).get("summary", {}).get("output_filename", "")
            output_path = OUTPUT_ROOT / f"{job_id}-port-fee-pdf" / filename
        if not output_path.is_file():
            self._send_json({"error": "导出文件不存在，请重新处理该任务"}, status=404)
            return
        record_export(
            DATABASE_PATH,
            task_id=job_id,
            export_type="port_fee_pdf_xlsx",
            file_path=output_path,
            owner=user,
        )
        self._send_download(output_path, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    def _handle_shipment_package_download(self, query: dict[str, list[str]]) -> None:
        user = self._require_auth()
        if not user:
            return
        batch_id = _first_query(query, "batch_id")
        filename = Path(_first_query(query, "filename")).name
        batch = BATCHES.get(batch_id)
        if not batch:
            history_item = get_task(DATABASE_PATH, batch_id)
            if not history_item:
                self._send_json({"error": "批次不存在或服务已重启"}, status=404)
                return
            if not _can_access_owner(user, history_item.get("owner_id", "")):
                self._send_json({"error": "没有权限下载该批次"}, status=403)
                return
            zip_path = OUTPUT_ROOT / f"{batch_id}-factory-packages" / filename
        elif not _can_access_owner(user, batch.owner_id):
            self._send_json({"error": "没有权限下载该批次"}, status=403)
            return
        else:
            package = next((item for item in SHIPMENT_PACKAGES.get(batch_id, []) if item.get("zip_filename") == filename), None)
            zip_path = Path(package["zip_path"]) if package else OUTPUT_ROOT / f"{batch_id}-factory-packages" / filename
        if not zip_path.is_file():
            self._send_json({"error": "打包文件已被移动或删除"}, status=404)
            return
        record_export(
            DATABASE_PATH,
            task_id=batch_id,
            export_type="shipment_factory_zip",
            file_path=zip_path,
            owner=user,
        )
        self._send_download(zip_path, "application/zip")

    def _handle_shipment_package_download_all(self, query: dict[str, list[str]]) -> None:
        user = self._require_auth()
        if not user:
            return
        batch_id = _first_query(query, "batch_id")
        batch = BATCHES.get(batch_id)
        if not batch:
            history_item = get_task(DATABASE_PATH, batch_id)
            if not history_item:
                self._send_json({"error": "批次不存在或服务已重启"}, status=404)
                return
            if not _can_access_owner(user, history_item.get("owner_id", "")):
                self._send_json({"error": "没有权限下载该批次"}, status=403)
                return
            zip_path = OUTPUT_ROOT / f"{batch_id}-factory-packages" / f"全部工厂-{batch_id}.zip"
        elif not _can_access_owner(user, batch.owner_id):
            self._send_json({"error": "没有权限下载该批次"}, status=403)
            return
        else:
            bundle = SHIPMENT_PACKAGE_BUNDLES.get(batch_id)
            zip_path = Path(bundle["zip_path"]) if bundle else OUTPUT_ROOT / f"{batch_id}-factory-packages" / f"全部工厂-{batch_id}.zip"
        if not zip_path.is_file():
            self._send_json({"error": "批量下载文件已被移动或删除"}, status=404)
            return
        record_export(
            DATABASE_PATH,
            task_id=batch_id,
            export_type="shipment_factory_zip_all",
            file_path=zip_path,
            owner=user,
        )
        self._send_download(zip_path, "application/zip")

    def _handle_shipment_selection_download(self, query: dict[str, list[str]]) -> None:
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
        package = next((item for item in SHIPMENT_SELECTED_PACKAGES.get(batch_id, []) if item.get("zip_filename") == filename), None)
        if not package:
            self._send_json({"error": "选中文件压缩包不存在"}, status=404)
            return
        zip_path = Path(package["zip_path"])
        if not zip_path.is_file():
            self._send_json({"error": "选中文件压缩包已被移动或删除"}, status=404)
            return
        record_export(
            DATABASE_PATH,
            task_id=batch_id,
            export_type="shipment_selected_pdf_zip",
            file_path=zip_path,
            owner=user,
        )
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
        record_operation(
            DATABASE_PATH,
            operation="shipment_rename",
            owner=user,
            target_id=batch.batch_id,
            target_type="shipment_pdf",
            message="批量重命名货件 PDF",
            payload={"renamed": sum(1 for plan in plans if plan.can_apply)},
        )
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
            self._send_json({"error": "按工厂/国家打包需要 confirm=true"}, status=400)
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
        bundle = _build_shipment_package_bundle(batch.batch_id, packages, result["package_root"])
        SHIPMENT_PACKAGE_BUNDLES[batch.batch_id] = bundle
        all_download = [{"label": "全部工厂/国家压缩包", "url": bundle["download_url"]}] if bundle else []
        _update_history_downloads(
            batch.batch_id,
            all_download + [{"label": f"{item['factory_name']} 压缩包", "url": item["download_url"]} for item in packages],
        )
        record_operation(
            DATABASE_PATH,
            operation="shipment_package_by_factory",
            owner=user,
            target_id=batch.batch_id,
            target_type="shipment_pdf",
            message="按工厂/国家打包货件 PDF",
            payload={"packages": len(packages), "skipped": result["skipped"]},
        )
        self._send_json(
            {
                "batch_id": batch.batch_id,
                "package_root": result["package_root"],
                "packages": packages,
                "bundle": bundle,
                "skipped": result["skipped"],
            }
        )

    def _handle_shipment_selection_package(self) -> None:
        user = self._require_auth()
        if not user:
            return
        payload = self._read_json()
        batch_id = str(payload.get("batch_id", ""))
        selected_paths = {str(path) for path in payload.get("source_paths", [])}
        batch = BATCHES.get(batch_id)
        if not batch:
            self._send_json({"error": "批次不存在或服务已重启"}, status=404)
            return
        if not _can_access_owner(user, batch.owner_id):
            self._send_json({"error": "没有权限打包该批次"}, status=403)
            return
        selected_records = [record for record in batch.records if str(record.source_path) in selected_paths]
        if not selected_records:
            self._send_json({"error": "请先勾选要下载的 PDF"}, status=400)
            return

        package_root = OUTPUT_ROOT / f"{batch.batch_id}-selected-packages"
        package_root.mkdir(parents=True, exist_ok=True)
        zip_filename = f"选中PDF-{batch.batch_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}.zip"
        zip_path = package_root / zip_filename
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for record in selected_records:
                if record.source_path.is_file():
                    archive.write(record.source_path, arcname=record.original_filename)
        package = {
            "zip_filename": zip_filename,
            "zip_path": str(zip_path),
            "download_url": (
                f"/api/shipment-selection/download?batch_id={batch.batch_id}"
                f"&filename={quote(zip_filename)}"
            ),
            "file_count": len(selected_records),
            "package_root": str(package_root),
        }
        SHIPMENT_SELECTED_PACKAGES.setdefault(batch.batch_id, []).append(package)
        record_operation(
            DATABASE_PATH,
            operation="shipment_selected_package",
            owner=user,
            target_id=batch.batch_id,
            target_type="shipment_pdf",
            message="打包下载选中的货件 PDF",
            payload={"files": len(selected_records)},
        )
        self._send_json({"batch_id": batch.batch_id, "package": package})

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def _send_json(self, payload: dict, status: int = 200, headers: dict[str, str] | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
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
            if key == "ops_toolbox_session":
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
    label_pages = sum(record.box_count for record in records)
    unique_carton_codes = len({code for record in records for code in record.carton_codes})
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    export_csv(records, OUTPUT_ROOT / f"{batch_id}-shipment-results.csv")
    export_xlsx(records, OUTPUT_ROOT / f"{batch_id}-shipment-results.xlsx")
    _record_history(
        task_id=batch_id,
        task_type="shipment_pdf",
        title="货件 PDF",
        source_label=source_label,
        summary={
            "files": len(records),
            "boxes": label_pages,
            "label_pages": label_pages,
            "unique_carton_codes": unique_carton_codes,
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


def _batch_payload(batch: BatchState, logs: list[dict] | None = None) -> dict:
    plans = plan_renames(batch.records)
    valid_count = sum(1 for record in batch.records if record.is_valid)
    label_pages = sum(record.box_count for record in batch.records)
    unique_carton_codes = len({code for record in batch.records for code in record.carton_codes})
    payload = {
        "batch_id": batch.batch_id,
        "source_label": batch.source_label,
        "summary": {
            "files": len(batch.records),
            "boxes": label_pages,
            "label_pages": label_pages,
            "unique_carton_codes": unique_carton_codes,
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
    if logs is not None:
        payload["logs"] = logs
    return payload


def _report_job_payload(job: ReportPdfJob) -> dict:
    return {
        "job_id": job.job_id,
        "source_label": job.source_label,
        "summary": job.summary,
        "rows": job.rows,
        "skipped_paths": job.summary.get("skipped_paths", []),
        "download_url": f"/api/report-pdf/download?job_id={job.job_id}",
    }


def _transaction_job_payload(job: TransactionCsvJob) -> dict:
    return {
        "job_id": job.job_id,
        "source_label": job.source_label,
        "summary": job.summary,
        "rows": job.rows,
        "countries": job.countries,
        "download_url": f"/api/transaction-csv/download?job_id={job.job_id}&file=total",
        "audit_download_url": f"/api/transaction-csv/download?job_id={job.job_id}&file=audit",
    }


def _walmart_transaction_job_payload(job: WalmartTransactionJob) -> dict:
    return {
        "job_id": job.job_id,
        "source_label": job.source_label,
        "summary": job.summary,
        "rows": job.rows,
        "download_url": f"/api/walmart-transaction/download?job_id={job.job_id}&file=total",
        "audit_download_url": f"/api/walmart-transaction/download?job_id={job.job_id}&file=audit",
    }


def _port_fee_job_payload(job: PortFeePdfJob) -> dict:
    return {
        "job_id": job.job_id,
        "source_label": job.source_label,
        "summary": job.summary,
        "rows": job.rows,
        "details": job.details,
        "skipped_paths": job.summary.get("skipped_paths", []),
        "download_url": f"/api/port-fee-pdf/download?job_id={job.job_id}",
    }


def _history_payload(user: dict) -> dict:
    tasks = [_task_with_available_downloads(task) for task in list_tasks(DATABASE_PATH, user)]
    return {
        "tasks": tasks,
        "summary": {
            "total": len(tasks),
            "shipment_pdf": sum(1 for task in tasks if task["type"] == "shipment_pdf"),
            "report_pdf": sum(1 for task in tasks if task["type"] == "report_pdf"),
            "transaction_csv": sum(1 for task in tasks if task["type"] == "transaction_csv"),
            "walmart_transaction": sum(1 for task in tasks if task["type"] == "walmart_transaction"),
            "port_fee_pdf": sum(1 for task in tasks if task["type"] == "port_fee_pdf"),
            "needs_review": sum(1 for task in tasks if task["status"] == "需复核"),
        },
    }


def _task_with_available_downloads(task: dict) -> dict:
    if task.get("type") != "shipment_pdf":
        return task

    task = dict(task)
    downloads = list(task.get("downloads", []))
    existing_urls = {item.get("url") for item in downloads}
    task_id = task.get("id", "")

    candidates = [
        ("CSV 文件", f"/api/export?batch_id={task_id}&format=csv", OUTPUT_ROOT / f"{task_id}-shipment-results.csv"),
        ("Excel 工作簿", f"/api/export?batch_id={task_id}&format=xlsx", OUTPUT_ROOT / f"{task_id}-shipment-results.xlsx"),
    ]
    for label, url, path in candidates:
        if path.is_file() and url not in existing_urls:
            downloads.append({"label": label, "url": url})
            existing_urls.add(url)

    package_root = OUTPUT_ROOT / f"{task_id}-factory-packages"
    if package_root.is_dir():
        package_paths = sorted(
            path for path in package_root.glob("*.zip")
            if path.is_file() and not path.name.startswith("全部工厂-")
        )
        bundle_path = package_root / f"全部工厂-{task_id}.zip"
        if package_paths and not bundle_path.is_file():
            _build_shipment_package_bundle(
                task_id,
                [{"zip_filename": path.name, "zip_path": str(path)} for path in package_paths],
                str(package_root),
            )
        all_url = f"/api/shipment-package/download-all?batch_id={task_id}"
        if bundle_path.is_file() and all_url not in existing_urls:
            downloads.append({"label": "全部工厂/国家压缩包", "url": all_url})
            existing_urls.add(all_url)
        for path in package_paths:
            url = f"/api/shipment-package/download?batch_id={task_id}&filename={quote(path.name)}"
            if url not in existing_urls:
                factory_name = path.name.removesuffix(".zip").removesuffix(f"-{task_id}")
                downloads.append({"label": f"{factory_name} 压缩包", "url": url})
                existing_urls.add(url)

    task["downloads"] = downloads
    return task


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
            "name": "电商经营数据工具箱",
            "address": f"http://{host}:{port}/",
            "status": "运行中",
        },
        "paths": {
            "project_root": str(PROJECT_ROOT.resolve()),
            "config_path": str(CONFIG.config_path.resolve()),
            "database_path": str(DATABASE_PATH.resolve()),
            "output_root": str(OUTPUT_ROOT.resolve()),
            "upload_root": str(UPLOAD_ROOT.resolve()),
            "backup_root": str(CONFIG.backup_root.resolve()),
            "allowed_input_roots": [str(root) for root in ALLOWED_INPUT_ROOTS],
        },
        "limits": {
            "max_upload_mb": CONFIG.max_upload_mb,
        },
        "processing": [
            {"name": "货件 PDF", "engine": "pdfplumber / pypdf 规则提取", "llm": "不依赖"},
            {"name": "汇总报告 PDF", "engine": "pdfplumber 表格结构解析 + 对账校验", "llm": "不依赖"},
            {"name": "交易明细 CSV/XLSX", "engine": "openpyxl / csv 规则清洗、字段翻译、记录类型分类", "llm": "不依赖"},
            {"name": "港杂费 PDF", "engine": "pdfplumber 文本坐标解析 + 金额合计校验", "llm": "不依赖"},
            {"name": "沃尔玛交易数据", "engine": "openpyxl 表头映射、字段翻译、汇率换算、审计输出", "llm": "不依赖"},
        ],
        "exports": ["CSV", "Excel"],
        "deployment_notes": [
            "当前服务可部署在公司内网机器上，由团队通过浏览器访问。",
            "上传文件写入 data/uploads，导出文件写入 data/outputs。",
            "历史任务、导出记录和操作日志已写入 SQLite，服务重启后可继续查看。",
            "端口、允许扫描目录和上传大小限制可通过 config/app-config.json 调整。",
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
    record_task(
        DATABASE_PATH,
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
        },
    )


def _update_history_downloads(task_id: str, downloads: list[dict]) -> None:
    update_task_downloads(DATABASE_PATH, task_id, downloads)


def _resolve_allowed_folder(folder_text: str) -> Path | None:
    folder = Path(folder_text).expanduser().resolve()
    for root in ALLOWED_INPUT_ROOTS:
        try:
            folder.relative_to(root)
            return folder
        except ValueError:
            continue
    return None


def _safe_upload_relative_path(raw_filename: str) -> Path | None:
    cleaned = raw_filename.replace("\\", "/").strip()
    parts = [_sanitize_upload_part(part) for part in cleaned.split("/")]
    parts = [part for part in parts if part and part not in {".", ".."}]
    if not parts:
        return None
    return Path(*parts)


def _upload_display_path(raw_filename: str) -> str:
    cleaned = raw_filename.replace("\\", "/").strip()
    return cleaned[:240] if cleaned else "未命名文件"


def _skipped_path_logs(paths: list[str], limit: int = 20) -> list[dict]:
    if not paths:
        return []
    logs = [{"level": "warning", "message": f"已跳过：{path}"} for path in paths[:limit]]
    if len(paths) > limit:
        logs.append({"level": "warning", "message": f"还有 {len(paths) - limit} 个已跳过文件未在日志中展开"})
    return logs


def _sanitize_upload_part(value: str) -> str:
    cleaned = value.strip().replace("\x00", "")
    for char in '<>:"|?*':
        cleaned = cleaned.replace(char, "")
    return cleaned[:120]


def _unique_upload_target(target: Path) -> Path:
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    parent = target.parent
    index = 2
    while True:
        candidate = parent / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def _allowed_roots_label() -> str:
    return "、".join(str(root) for root in ALLOWED_INPUT_ROOTS)


def _new_batch_id() -> str:
    return uuid.uuid4().hex[:12]


def _can_access_owner(user: dict, owner_id: str) -> bool:
    return user.get("role") == "admin" or user.get("id") == owner_id


def _active_admin_count(users: list[dict]) -> int:
    return sum(1 for user in users if user.get("role") == "admin" and user.get("active", True))


def _session_cookie(token: str) -> str:
    return f"ops_toolbox_session={token}; Path=/; HttpOnly; SameSite=Lax"


def _clear_session_cookie() -> str:
    return "ops_toolbox_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"


def _now_label() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _first_query(query: dict[str, list[str]], key: str) -> str:
    values = query.get(key, [])
    return values[0] if values else ""


def _ascii_download_filename(filename: str) -> str:
    cleaned = "".join(char if 32 <= ord(char) < 127 and char not in {'"', "\\"} else "_" for char in filename)
    return cleaned or "download"


def _build_shipment_package_bundle(batch_id: str, packages: list[dict], package_root: str) -> dict:
    if not packages:
        return {}
    bundle_filename = f"全部工厂-{batch_id}.zip"
    bundle_path = Path(package_root) / bundle_filename
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for package in packages:
            package_path = Path(package["zip_path"])
            if package_path.is_file():
                archive.write(package_path, arcname=package["zip_filename"])
    return {
        "zip_filename": bundle_filename,
        "zip_path": str(bundle_path),
        "download_url": f"/api/shipment-package/download-all?batch_id={batch_id}",
        "package_count": len(packages),
    }


def _remove_task_artifacts(task: dict) -> int:
    task_id = task.get("id", "")
    if not task_id:
        return 0
    candidates: list[Path] = []
    task_type = task.get("type")
    if task_type == "shipment_pdf":
        candidates.extend([
            OUTPUT_ROOT / f"{task_id}-shipment-results.csv",
            OUTPUT_ROOT / f"{task_id}-shipment-results.xlsx",
            OUTPUT_ROOT / f"{task_id}-factory-packages",
            OUTPUT_ROOT / f"{task_id}-selected-pdfs.zip",
            UPLOAD_ROOT / task_id,
        ])
    elif task_type == "report_pdf":
        candidates.extend([
            OUTPUT_ROOT / f"{task_id}-amazon-report-pdf-results.xlsx",
            UPLOAD_ROOT / f"{task_id}-report-pdf",
        ])
    elif task_type == "transaction_csv":
        candidates.extend([
            OUTPUT_ROOT / f"{task_id}-transaction-csv",
            UPLOAD_ROOT / f"{task_id}-transaction-csv",
        ])
    elif task_type == "walmart_transaction":
        candidates.extend([
            OUTPUT_ROOT / f"{task_id}-walmart-transaction",
            UPLOAD_ROOT / f"{task_id}-walmart-transaction",
        ])
    elif task_type == "port_fee_pdf":
        candidates.extend([
            OUTPUT_ROOT / f"{task_id}-port-fee-pdf",
            UPLOAD_ROOT / f"{task_id}-port-fee-pdf",
        ])

    removed = 0
    for path in candidates:
        removed += _safe_remove_generated_path(path)
    return removed


def _safe_remove_generated_path(path: Path) -> int:
    try:
        resolved = path.resolve()
        allowed_roots = [OUTPUT_ROOT.resolve(), UPLOAD_ROOT.resolve()]
        if not any(resolved == root or root in resolved.parents for root in allowed_roots):
            return 0
        if resolved.is_dir():
            shutil.rmtree(resolved)
            return 1
        if resolved.is_file():
            resolved.unlink()
            return 1
    except FileNotFoundError:
        return 0
    return 0


def run(host: str | None = None, port: int | None = None) -> None:
    host = host or CONFIG.host
    port = port or CONFIG.port
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    DEFAULT_INPUT_ROOT.mkdir(parents=True, exist_ok=True)
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    CONFIG.backup_root.mkdir(parents=True, exist_ok=True)
    ensure_user_store(USER_STORE)
    init_db(DATABASE_PATH)
    server = ThreadingHTTPServer((host, port), AmazonToolboxHandler)
    print(f"Ops Toolbox running at http://{host}:{port}/")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ops Toolbox")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()
