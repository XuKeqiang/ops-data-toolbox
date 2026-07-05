from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.amazon_toolbox.config import load_config
from app.amazon_toolbox.storage import (
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


class ConfigStorageTests(unittest.TestCase):
    def test_load_config_from_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "app-config.json"
            allowed_root = root / "incoming"
            payload = {
                "server": {"host": "0.0.0.0", "port": 18080},
                "paths": {
                    "data_root": str(root / "runtime"),
                    "upload_root": str(root / "runtime" / "uploads"),
                    "output_root": str(root / "runtime" / "outputs"),
                    "database_path": str(root / "runtime" / "toolbox.sqlite3"),
                    "user_store": str(root / "runtime" / "users.json"),
                    "allowed_input_roots": [str(allowed_root)],
                },
                "limits": {"max_upload_mb": 12},
                "backups": {"backup_root": str(root / "backups"), "retention_days": 5},
            }
            config_path.write_text(json.dumps(payload), "utf-8")

            config = load_config(config_path)

            self.assertEqual(config.host, "0.0.0.0")
            self.assertEqual(config.port, 18080)
            self.assertEqual(config.database_path, root / "runtime" / "toolbox.sqlite3")
            self.assertEqual(config.allowed_input_roots, (allowed_root.resolve(),))
            self.assertEqual(config.max_upload_mb, 12)
            self.assertEqual(config.backup_retention_days, 5)

    def test_storage_records_tasks_exports_and_operations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "app.sqlite3"
            owner = {
                "id": "u1",
                "username": "admin",
                "display_name": "Admin",
                "role": "admin",
            }
            init_db(db_path)

            record_task(
                db_path,
                {
                    "id": "task1",
                    "type": "shipment_pdf",
                    "title": "货件 PDF",
                    "source_label": "sample",
                    "created_at": "2026-06-28 10:00:00",
                    "summary": {"files": 2},
                    "status": "完成",
                    "downloads": [{"label": "CSV", "url": "/api/export?task1"}],
                    "owner_id": owner["id"],
                    "owner_name": owner["display_name"],
                    "owner_username": owner["username"],
                },
            )
            update_task_downloads(
                db_path,
                "task1",
                [{"label": "Excel", "url": "/api/export?task1&format=xlsx"}],
            )
            export_path = Path(tmp) / "result.xlsx"
            export_path.write_text("ok", "utf-8")
            record_export(
                db_path,
                task_id="task1",
                export_type="shipment_xlsx",
                file_path=export_path,
                owner=owner,
            )
            record_operation(
                db_path,
                operation="shipment_export",
                owner=owner,
                target_id="task1",
                target_type="shipment_pdf",
                message="导出测试",
            )

            task = get_task(db_path, "task1")
            self.assertIsNotNone(task)
            self.assertEqual(task["summary"]["files"], 2)
            self.assertEqual(len(task["downloads"]), 2)
            self.assertEqual(list_tasks(db_path, owner)[0]["id"], "task1")

            self.assertTrue(delete_task(db_path, "task1"))
            self.assertIsNone(get_task(db_path, "task1"))

    def test_storage_prunes_old_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "app.sqlite3"
            owner = {
                "id": "u1",
                "username": "admin",
                "display_name": "Admin",
                "role": "admin",
            }
            for task_id, created_at in [
                ("old-task", "2020-01-01 10:00:00"),
                ("new-task", "2099-01-01 10:00:00"),
            ]:
                record_task(
                    db_path,
                    {
                        "id": task_id,
                        "type": "report_pdf",
                        "title": "汇总报告 PDF",
                        "source_label": "sample",
                        "created_at": created_at,
                        "summary": {"files": 1},
                        "status": "完成",
                        "downloads": [],
                        "owner_id": owner["id"],
                        "owner_name": owner["display_name"],
                        "owner_username": owner["username"],
                    },
                )

            pruned = prune_tasks(db_path, owner, days=30)

            self.assertEqual([task["id"] for task in pruned], ["old-task"])
            self.assertIsNone(get_task(db_path, "old-task"))
            self.assertIsNotNone(get_task(db_path, "new-task"))


if __name__ == "__main__":
    unittest.main()
