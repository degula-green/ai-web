# -*- coding: utf-8 -*-
"""
Main project auth adapter for ContentRemixAgent.

This adapter validates bearer tokens issued by the main project IAM system
and returns a lightweight user object used by remix APIs.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Optional

import jwt
from sqlalchemy import text

from db.base import get_async_session


@dataclass
class User:
    """Minimal user model used by remix routes."""

    user_id: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    status: int = 1
    email_verified_at: Optional[datetime] = None


class MainAuthAdapter:
    """Validate main-project access token and resolve IAM user."""

    def __init__(self) -> None:
        self.jwt_secret = self._read_env_value("AUTH_JWT_SECRET")
        self.jwt_algorithm = self._read_env_value("AUTH_JWT_ALGORITHM") or "HS256"

    @staticmethod
    def _read_env_value(name: str) -> str:
        direct = (os.getenv(name) or "").strip()
        if direct:
            return direct

        env_path = Path(__file__).resolve().parents[2] / ".env"
        if not env_path.exists():
            return ""

        try:
            for raw_line in env_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                if key.strip() != name:
                    continue
                resolved = value.strip()
                if (
                    resolved
                    and len(resolved) >= 2
                    and resolved[0] == resolved[-1]
                    and resolved[0] in {"'", '"'}
                ):
                    resolved = resolved[1:-1]
                return resolved
        except OSError:
            return ""

        return ""

    def verify_access_token(self, token: str) -> Optional[int]:
        if not self.jwt_secret:
            return None
        try:
            claims = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
        except Exception:
            return None

        if claims.get("typ") != "access":
            return None

        user_id_raw = claims.get("sub")
        session_id = claims.get("sid")
        if user_id_raw is None or not session_id:
            return None
        try:
            return int(user_id_raw)
        except (TypeError, ValueError):
            return None

    async def get_user_by_token(self, token: str) -> Optional[User]:
        user_id = self.verify_access_token(token)
        if user_id is None:
            return None

        token_digest = sha256(token.encode("utf-8")).hexdigest()
        now = datetime.now(timezone.utc)

        async with get_async_session() as session:
            session_row = (
                await session.execute(
                    text(
                        """
                        SELECT s.session_id, s.user_id, s.session_status, s.expired_at
                        FROM iam_sessions s
                        WHERE s.user_id = :uid
                          AND s.access_token_digest = :token_digest
                        ORDER BY s.updated_at DESC, s.id DESC
                        LIMIT 1
                        """
                    ),
                    {"uid": user_id, "token_digest": token_digest},
                )
            ).mappings().fetchone()

            if not session_row or session_row["session_status"] != "active":
                return None

            expired_at = session_row.get("expired_at")
            if expired_at is not None:
                exp_aware = expired_at if expired_at.tzinfo else expired_at.replace(tzinfo=timezone.utc)
                if exp_aware < now:
                    return None

            user_row = (
                await session.execute(
                    text(
                        """
                        SELECT id, email, nickname, avatar_url, status
                        FROM iam_users
                        WHERE id = :uid
                          AND is_deleted = 0
                        LIMIT 1
                        """
                    ),
                    {"uid": user_id},
                )
            ).mappings().fetchone()

            if not user_row:
                return None

            status_text = (user_row.get("status") or "").lower()
            if status_text in {"disabled", "locked"}:
                return None

            return User(
                user_id=str(user_row["id"]),
                email=user_row.get("email"),
                display_name=user_row.get("nickname"),
                avatar_url=user_row.get("avatar_url"),
                status=1,
                email_verified_at=None,
            )


main_auth_adapter = MainAuthAdapter()

