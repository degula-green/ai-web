from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app.utils.ids import generate_id


def generate_request_id() -> str:
    return generate_id("req")


def generate_session_id() -> str:
    return generate_id("sess")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_salt(length: int = 16) -> str:
    return secrets.token_hex(length)


def hash_password(password: str, salt: str, iterations: int) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations).hex()


def verify_password(password: str, stored_hash: str | None, salt: str | None, iterations: int) -> bool:
    if not stored_hash or not salt:
        return False
    candidate = hash_password(password, salt, iterations)
    return hmac.compare_digest(candidate, stored_hash)


def create_access_token(*, secret: str, algorithm: str, user_id: int, session_id: str, expires_in: int) -> str:
    payload = {
        "sub": str(user_id),
        "sid": session_id,
        "typ": "access",
        "iat": int(utc_now().timestamp()),
        "exp": int((utc_now() + timedelta(seconds=expires_in)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def create_refresh_token(*, secret: str, algorithm: str, user_id: int, session_id: str, expires_in: int) -> str:
    payload = {
        "sub": str(user_id),
        "sid": session_id,
        "typ": "refresh",
        "iat": int(utc_now().timestamp()),
        "exp": int((utc_now() + timedelta(seconds=expires_in)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_token(token: str, *, secret: str, algorithm: str) -> dict:
    return jwt.decode(token, secret, algorithms=[algorithm])


def digest_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def format_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%Y-%m-%d %H:%M:%S")
