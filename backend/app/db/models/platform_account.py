from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PlatformAccount(Base):
    """Third-party platform account profile."""

    __tablename__ = "platform_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_user_id: Mapped[int] = mapped_column(Integer, index=True, comment="Owner user id")
    platform_code: Mapped[str] = mapped_column(String(32), index=True, comment="Platform code")
    account_name: Mapped[str] = mapped_column(String(128), comment="Login/account name")
    account_pwd_encrypted: Mapped[str | None] = mapped_column(String(512), comment="Encrypted password")
    nickname: Mapped[str | None] = mapped_column(String(128), comment="Nickname on platform")
    avatar_url: Mapped[str | None] = mapped_column(String(512), comment="Avatar URL")
    platform_uid: Mapped[str | None] = mapped_column(String(128), index=True, comment="Platform UID")
    identity_type: Mapped[str | None] = mapped_column(String(32), index=True, comment="Primary identity type")
    identity_value: Mapped[str | None] = mapped_column(String(255), index=True, comment="Primary identity value")
    sec_user_id: Mapped[str | None] = mapped_column(String(255), index=True, comment="Stable sec_user_id")
    identity_fallback: Mapped[str | None] = mapped_column(String(128), comment="Fallback identity value")
    identity_source: Mapped[str | None] = mapped_column(String(32), comment="Fallback identity source")
    auth_status: Mapped[str] = mapped_column(String(32), default="need_reauth", index=True, comment="Auth status")
    account_status: Mapped[str] = mapped_column(String(32), default="needs_rebind", index=True, comment="Account status")
    last_identity_verified_at: Mapped[datetime | None] = mapped_column(DateTime, comment="Last identity verified time")
    last_identity_error: Mapped[str | None] = mapped_column(String(500), comment="Last identity validation error")
    account_type: Mapped[str] = mapped_column(String(32), default="personal", comment="Account type")
    tags: Mapped[dict | None] = mapped_column(JSON, comment="Tags")
    remark: Mapped[str | None] = mapped_column(String(500), comment="Remarks")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, comment="Soft delete")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class PlatformAccountSession(Base):
    """Persisted authorization/session snapshot for a platform account."""

    __tablename__ = "platform_account_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, comment="Platform account id")
    cookies: Mapped[list | None] = mapped_column(JSON, comment="Cookie snapshot (legacy compatible)")
    local_storage: Mapped[dict | None] = mapped_column(JSON, comment="LocalStorage snapshot")
    session_token: Mapped[str | None] = mapped_column(Text, comment="Optional session token")
    user_agent: Mapped[str | None] = mapped_column(String(512), comment="User-Agent")
    device_info: Mapped[dict | None] = mapped_column(JSON, comment="Device fingerprint metadata")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, comment="Session expiration time")
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, comment="Last sync time")
    auth_type: Mapped[str] = mapped_column(String(32), default="cookie", comment="Auth type: cookie/qrcode/phone")
    cookie_blob: Mapped[str | None] = mapped_column(Text, comment="Encrypted cookie blob")
    status: Mapped[str] = mapped_column(String(32), default="active", comment="Session status")
    session_status: Mapped[str] = mapped_column(String(32), default="active", index=True, comment="Normalized session status")
    cookie_hash: Mapped[str | None] = mapped_column(String(128), comment="Cookie hash")
    storage_hash: Mapped[str | None] = mapped_column(String(128), comment="Local storage hash")
    source_type: Mapped[str | None] = mapped_column(String(32), comment="Session source type")
    source_client_id: Mapped[str | None] = mapped_column(String(128), comment="Session source client id")
    validated_identity: Mapped[str | None] = mapped_column(String(255), comment="Last validated identity value")
    last_validation_error: Mapped[str | None] = mapped_column(String(500), comment="Last validation error")
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime, comment="Last validated timestamp")
    last_refresh_at: Mapped[datetime | None] = mapped_column(DateTime, comment="Last refresh timestamp")
    encrypt_key_id: Mapped[str | None] = mapped_column(String(64), comment="Encryption key identifier")
    cookie_version: Mapped[int] = mapped_column(Integer, default=1, comment="Cookie version for rotation")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class CrawlerCookieAccountBinding(Base):
    """Bind a main-system user/account to a MediaCrawler cookie account row."""

    __tablename__ = "crawler_cookie_account_bindings"
    __table_args__ = (
        UniqueConstraint(
            "owner_user_id",
            "platform_code",
            "crawler_cookie_account_id",
            name="uk_ccab_user_platform_crawler",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    owner_user_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="Owner user id")
    platform_code: Mapped[str] = mapped_column(String(32), index=True, comment="Main platform code, e.g. douyin")
    platform_account_id: Mapped[int | None] = mapped_column(
        BigInteger,
        index=True,
        comment="Optional platform_accounts.id",
    )
    crawler_cookie_account_id: Mapped[int] = mapped_column(
        BigInteger,
        index=True,
        comment="crawler_cookies_account.id",
    )
    status: Mapped[str] = mapped_column(String(32), default="active", index=True, comment="active/disabled")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, comment="Preferred account for the user/platform")
    priority: Mapped[int] = mapped_column(Integer, default=100, comment="Lower value wins")
    remark: Mapped[str | None] = mapped_column(String(500), comment="Remarks")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class PlatformCookieBridgeBinding(Base):
    """Bind a main-system user/account to a CookieBridge client id."""

    __tablename__ = "platform_cookie_bridge_bindings"
    __table_args__ = (
        UniqueConstraint(
            "owner_user_id",
            "platform_code",
            "bridge_client_id",
            name="uk_pcbb_user_platform_client",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    owner_user_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="Owner user id")
    platform_code: Mapped[str] = mapped_column(String(32), index=True, comment="Main platform code")
    bridge_client_id: Mapped[str] = mapped_column(String(128), index=True, comment="CookieBridge client_id")
    platform_account_id: Mapped[int | None] = mapped_column(BigInteger, index=True, comment="platform_accounts.id")
    crawler_cookie_account_id: Mapped[int | None] = mapped_column(
        BigInteger,
        index=True,
        comment="crawler_cookies_account.id",
    )
    status: Mapped[str] = mapped_column(String(32), default="active", index=True, comment="active/disabled")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, comment="Preferred bridge client")
    last_reported_identity: Mapped[str | None] = mapped_column(String(255), comment="Last reported identity value")
    last_reported_nickname: Mapped[str | None] = mapped_column(String(255), comment="Last reported nickname")
    last_cookie_hash: Mapped[str | None] = mapped_column(String(128), comment="Last reported cookie hash")
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, comment="Last CookieBridge sync time")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class PlatformAccountAuthLog(Base):
    """Audit log for auth lifecycle events."""

    __tablename__ = "platform_account_auth_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, index=True, comment="Platform account id")
    event_type: Mapped[str] = mapped_column(String(32), comment="bind/refresh/expire/revoke")
    event_status: Mapped[str] = mapped_column(String(32), comment="success/failed")
    fail_reason: Mapped[str | None] = mapped_column(String(500), comment="Failure reason")
    ip_address: Mapped[str | None] = mapped_column(String(64), comment="Source IP")
    extra_data: Mapped[dict | None] = mapped_column(JSON, comment="Extra metadata")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
