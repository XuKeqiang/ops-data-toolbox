from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.ops_toolbox import server


RUNNER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "web-update-runner.py"
RUNNER_SPEC = importlib.util.spec_from_file_location("web_update_runner", RUNNER_PATH)
assert RUNNER_SPEC and RUNNER_SPEC.loader
web_update_runner = importlib.util.module_from_spec(RUNNER_SPEC)
RUNNER_SPEC.loader.exec_module(web_update_runner)


class SystemUpdateTest(unittest.TestCase):
    def test_runner_uses_powershell_on_windows(self) -> None:
        command = web_update_runner.update_command("nt")
        self.assertEqual(command[0], "powershell.exe")
        self.assertIn(r".\scripts\update.ps1", command)

    def test_runner_uses_bash_on_macos_and_linux(self) -> None:
        self.assertEqual(web_update_runner.update_command("posix"), ["bash", "scripts/update.sh"])

    def test_check_reports_remote_update(self) -> None:
        values = {
            ("branch", "--show-current"): "main",
            ("status", "--short"): "",
            ("rev-parse", "HEAD"): "local-full",
            ("rev-parse", "--short", "HEAD"): "local1",
            ("fetch", "--prune", "origin"): "",
            ("rev-parse", "origin/main"): "remote-full",
            ("rev-parse", "--short", "origin/main"): "remote2",
            ("rev-list", "--count", "HEAD..origin/main"): "2",
            ("rev-list", "--count", "origin/main..HEAD"): "0",
        }
        with patch.object(server, "_run_git", side_effect=lambda *args, **kwargs: values[args]):
            result = server._check_system_update()
        self.assertTrue(result["update_available"])
        self.assertEqual(result["behind"], 2)
        self.assertFalse(result["dirty"])

    def test_check_surfaces_local_changes(self) -> None:
        values = {
            ("branch", "--show-current"): "main",
            ("status", "--short"): " M config/local.json",
            ("rev-parse", "HEAD"): "same-full",
            ("rev-parse", "--short", "HEAD"): "same1",
            ("fetch", "--prune", "origin"): "",
            ("rev-parse", "origin/main"): "same-full",
            ("rev-parse", "--short", "origin/main"): "same1",
            ("rev-list", "--count", "HEAD..origin/main"): "0",
            ("rev-list", "--count", "origin/main..HEAD"): "0",
        }
        with patch.object(server, "_run_git", side_effect=lambda *args, **kwargs: values[args]):
            result = server._check_system_update()
        self.assertTrue(result["dirty"])
        self.assertEqual(result["changes"], [" M config/local.json"])

    def test_update_status_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            status_path = Path(temp_dir) / "status.json"
            with patch.object(server, "UPDATE_STATUS_PATH", status_path):
                server._write_update_status({"token": "secret", "phase": "queued"})
                self.assertEqual(server._read_update_status()["phase"], "queued")


if __name__ == "__main__":
    unittest.main()
