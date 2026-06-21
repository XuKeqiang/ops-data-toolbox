from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import uuid
from pathlib import Path


PASSWORD_ITERATIONS = 210_000


def ensure_user_store(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    password = os.environ.get("AMAZON_TOOLBOX_ADMIN_PASSWORD", "admin123")
    now = _now_label()
    user = {
        "id": uuid.uuid4().hex,
        "username": "admin",
        "display_name": "系统管理员",
        "role": "admin",
        "active": True,
        "password_hash": hash_password(password),
        "created_at": now,
        "updated_at": now,
    }
    save_users(path, [user])


def load_users(path: Path) -> list[dict]:
    ensure_user_store(path)
    return json.loads(path.read_text("utf-8"))


def save_users(path: Path, users: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(users, ensure_ascii=False, indent=2), "utf-8")


def public_user(user: dict | None) -> dict | None:
    if not user:
        return None
    return {
        "id": user["id"],
        "username": user["username"],
        "display_name": user.get("display_name") or user["username"],
        "role": user["role"],
        "active": bool(user.get("active", True)),
        "created_at": user.get("created_at", ""),
        "updated_at": user.get("updated_at", ""),
    }


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (TypeError, ValueError):
        return False


def validate_role(role: str) -> str:
    return role if role in {"admin", "operator"} else "operator"


def find_user_by_id(users: list[dict], user_id: str) -> dict | None:
    return next((user for user in users if user["id"] == user_id), None)


def find_user_by_username(users: list[dict], username: str) -> dict | None:
    normalized = normalize_username(username)
    return next((user for user in users if user["username"].lower() == normalized), None)


def normalize_username(username: str) -> str:
    return username.strip().lower()


def _now_label() -> str:
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
