from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import AuthSettings
from app.utils.ids import generate_id


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_salt() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(16)).decode("utf-8").rstrip("=")


def hash_password(password: str, salt: str) -> str:
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 240000)
    return base64.urlsafe_b64encode(derived).decode("utf-8").rstrip("=")


def verify_password(password: str, *, salt: str | None, expected_hash: str | None) -> bool:
    if not salt or not expected_hash:
        return False
    actual = hash_password(password, salt)
    return hmac.compare_digest(actual, expected_hash)


def digest_token(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_access_token(payload: dict[str, Any], settings: AuthSettings) -> tuple[str, datetime]:
    expires_at = utc_now() + timedelta(seconds=settings.access_token_ttl_seconds)
    token = jwt.encode({**payload, "exp": expires_at, "typ": "access"}, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_at


def decode_access_token(token: str, settings: AuthSettings) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def build_refresh_token() -> str:
    return f"refresh_{secrets.token_urlsafe(32)}"


def build_session_id() -> str:
    return generate_id("sess")
