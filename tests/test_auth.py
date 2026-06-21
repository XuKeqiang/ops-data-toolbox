import tempfile
from pathlib import Path
from unittest import TestCase

from app.amazon_toolbox.auth import ensure_user_store, load_users, normalize_username, verify_password


class AuthTest(TestCase):
    def test_ensure_user_store_creates_default_admin(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "users.json"

            ensure_user_store(path)
            users = load_users(path)

            self.assertEqual(len(users), 1)
            self.assertEqual(users[0]["username"], "admin")
            self.assertEqual(users[0]["role"], "admin")
            self.assertTrue(verify_password("admin123", users[0]["password_hash"]))

    def test_normalize_username(self) -> None:
        self.assertEqual(normalize_username("  AdminUser  "), "adminuser")
