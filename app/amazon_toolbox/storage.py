from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def init_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                source_label TEXT NOT NULL,
                created_at TEXT NOT NULL,
                summary_json TEXT NOT NULL,
                status TEXT NOT NULL,
                downloads_json TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                owner_name TEXT NOT NULL,
                owner_username TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS export_records (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                export_type TEXT NOT NULL,
                filename TEXT NOT NULL,
                path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                owner_name TEXT NOT NULL,
                owner_username TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS operation_logs (
                id TEXT PRIMARY KEY,
                operation TEXT NOT NULL,
                target_id TEXT,
                target_type TEXT,
                status TEXT NOT NULL,
                message TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                owner_name TEXT NOT NULL,
                owner_username TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_tasks_owner ON tasks(owner_id);
            CREATE INDEX IF NOT EXISTS idx_exports_task ON export_records(task_id);
            CREATE INDEX IF NOT EXISTS idx_logs_created_at ON operation_logs(created_at DESC);
            """
        )


def record_task(path: Path, task: dict[str, Any]) -> None:
    init_db(path)
    with _connect(path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO tasks (
                id, type, title, source_label, created_at, summary_json, status,
                downloads_json, owner_id, owner_name, owner_username
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task["id"],
                task["type"],
                task["title"],
                task.get("source_label", ""),
                task.get("created_at") or _now_label(),
                json.dumps(task.get("summary", {}), ensure_ascii=False),
                task.get("status", "完成"),
                json.dumps(task.get("downloads", []), ensure_ascii=False),
                task.get("owner_id", ""),
                task.get("owner_name", ""),
                task.get("owner_username", ""),
            ),
        )


def list_tasks(path: Path, user: dict[str, Any], limit: int = 200) -> list[dict[str, Any]]:
    init_db(path)
    sql = "SELECT * FROM tasks"
    params: list[Any] = []
    if user.get("role") != "admin":
        sql += " WHERE owner_id = ?"
        params.append(user.get("id", ""))
    sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
    params.append(limit)
    with _connect(path) as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_task_from_row(row) for row in rows]


def get_task(path: Path, task_id: str) -> dict[str, Any] | None:
    init_db(path)
    with _connect(path) as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return _task_from_row(row) if row else None


def delete_task(path: Path, task_id: str) -> bool:
    init_db(path)
    with _connect(path) as conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.execute("DELETE FROM export_records WHERE task_id = ?", (task_id,))
        conn.execute("DELETE FROM operation_logs WHERE target_id = ?", (task_id,))
    return cursor.rowcount > 0


def prune_tasks(path: Path, user: dict[str, Any], days: int) -> list[dict[str, Any]]:
    init_db(path)
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    sql = "SELECT * FROM tasks WHERE created_at < ?"
    params: list[Any] = [cutoff]
    if user.get("role") != "admin":
        sql += " AND owner_id = ?"
        params.append(user.get("id", ""))
    with _connect(path) as conn:
        rows = conn.execute(sql, params).fetchall()
    tasks = [_task_from_row(row) for row in rows]
    for task in tasks:
        delete_task(path, task["id"])
    return tasks


def update_task_downloads(path: Path, task_id: str, downloads: list[dict[str, Any]]) -> None:
    task = get_task(path, task_id)
    if not task:
        return
    existing_urls = {item.get("url") for item in task.get("downloads", [])}
    task["downloads"].extend(item for item in downloads if item.get("url") not in existing_urls)
    record_task(path, task)


def record_export(
    path: Path,
    *,
    task_id: str,
    export_type: str,
    file_path: Path,
    owner: dict[str, Any],
) -> None:
    init_db(path)
    with _connect(path) as conn:
        conn.execute(
            """
            INSERT INTO export_records (
                id, task_id, export_type, filename, path, created_at,
                owner_id, owner_name, owner_username
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                uuid.uuid4().hex,
                task_id,
                export_type,
                file_path.name,
                str(file_path),
                _now_label(),
                owner.get("id", ""),
                owner.get("display_name") or owner.get("username", ""),
                owner.get("username", ""),
            ),
        )


def record_operation(
    path: Path,
    *,
    operation: str,
    owner: dict[str, Any],
    target_id: str = "",
    target_type: str = "",
    status: str = "success",
    message: str = "",
    payload: dict[str, Any] | None = None,
) -> None:
    init_db(path)
    with _connect(path) as conn:
        conn.execute(
            """
            INSERT INTO operation_logs (
                id, operation, target_id, target_type, status, message, payload_json,
                created_at, owner_id, owner_name, owner_username
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                uuid.uuid4().hex,
                operation,
                target_id,
                target_type,
                status,
                message,
                json.dumps(payload or {}, ensure_ascii=False),
                _now_label(),
                owner.get("id", ""),
                owner.get("display_name") or owner.get("username", ""),
                owner.get("username", ""),
            ),
        )


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _task_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "type": row["type"],
        "title": row["title"],
        "source_label": row["source_label"],
        "created_at": row["created_at"],
        "summary": json.loads(row["summary_json"] or "{}"),
        "status": row["status"],
        "downloads": json.loads(row["downloads_json"] or "[]"),
        "owner_id": row["owner_id"],
        "owner_name": row["owner_name"],
        "owner_username": row["owner_username"],
    }


def _now_label() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
