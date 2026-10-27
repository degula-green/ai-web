from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IAMUser(Base):
    __tablename__ = "iam_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_no: Mapped[str] = mapped_column(String(64))
    username: Mapped[str | None] = mapped_column(String(64))
    nickname: Mapped[str] = mapped_column(String(64))
    real_name: Mapped[str | None] = mapped_column(String(64))
    avatar_url: Mapped[str | None] = mapped_column(String(255))
    gender: Mapped[int] = mapped_column(Integer)
    phone: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32))
    user_type: Mapped[str] = mapped_column(String(32))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_login_ip: Mapped[str | None] = mapped_column(String(64))
    remark: Mapped[str | None] = mapped_column(String(500))
    is_deleted: Mapped[bool]
    created_by: Mapped[int]
    updated_by: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class IAMUserIdentity(Base):
    __tablename__ = "iam_user_identities"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int]
    identity_type: Mapped[str] = mapped_column(String(32))
    identity_key: Mapped[str] = mapped_column(String(128))
    identity_value: Mapped[str | None] = mapped_column(String(255))
    credential_hash: Mapped[str | None] = mapped_column(String(255))
    credential_salt: Mapped[str | None] = mapped_column(String(128))
    verify_status: Mapped[str] = mapped_column(String(32))
    is_primary: Mapped[bool]
    is_enabled: Mapped[bool]
    bound_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime)
    expired_at: Mapped[datetime | None] = mapped_column(DateTime)
    extra_data: Mapped[dict | None] = mapped_column(JSON)
    remark: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class IAMRole(Base):
    __tablename__ = "iam_roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    role_code: Mapped[str] = mapped_column(String(64))
    role_name: Mapped[str] = mapped_column(String(64))
    role_type: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32))
    sort_order: Mapped[int]
    description: Mapped[str | None] = mapped_column(String(500))
    is_builtin: Mapped[bool]
    is_deleted: Mapped[bool]
    created_by: Mapped[int]
    updated_by: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class IAMPermission(Base):
    __tablename__ = "iam_permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    permission_code: Mapped[str] = mapped_column(String(128))
    permission_name: Mapped[str] = mapped_column(String(128))
    module_code: Mapped[str] = mapped_column(String(64))
    action_code: Mapped[str] = mapped_column(String(64))
    permission_type: Mapped[str] = mapped_column(String(32))
    parent_id: Mapped[int | None]
    path: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32))
    sort_order: Mapped[int]
    description: Mapped[str | None] = mapped_column(String(500))
    is_builtin: Mapped[bool]
    is_deleted: Mapped[bool]
    created_by: Mapped[int]
    updated_by: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class IAMRolePermission(Base):
    __tablename__ = "iam_role_permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int]
    permission_id: Mapped[int]
    granted_by: Mapped[int]
    granted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    status: Mapped[str] = mapped_column(String(32))
    remark: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class IAMUserRole(Base):
    __tablename__ = "iam_user_roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int]
    role_id: Mapped[int]
    assigned_by: Mapped[int]
    assigned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expired_at: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(32))
    remark: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class IAMSession(Base):
    __tablename__ = "iam_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(128))
    user_id: Mapped[int]
    identity_id: Mapped[int]
    login_type: Mapped[str] = mapped_column(String(32))
    access_token_digest: Mapped[str | None] = mapped_column(String(128))
    refresh_token_digest: Mapped[str | None] = mapped_column(String(128))
    device_type: Mapped[str] = mapped_column(String(32))
    device_id: Mapped[str | None] = mapped_column(String(128))
    client_version: Mapped[str | None] = mapped_column(String(64))
    os_name: Mapped[str | None] = mapped_column(String(64))
    browser_name: Mapped[str | None] = mapped_column(String(64))
    ip_address: Mapped[str | None] = mapped_column(String(64))
    ip_location: Mapped[str | None] = mapped_column(String(255))
    user_agent: Mapped[str | None] = mapped_column(Text)
    login_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime)
    expired_at: Mapped[datetime | None] = mapped_column(DateTime)
    logout_at: Mapped[datetime | None] = mapped_column(DateTime)
    session_status: Mapped[str] = mapped_column(String(32))
    revoke_reason: Mapped[str | None] = mapped_column(String(255))
    extra_data: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class IAMLoginLog(Base):
    __tablename__ = "iam_login_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None]
    identity_id: Mapped[int | None]
    login_type: Mapped[str] = mapped_column(String(32))
    login_identifier: Mapped[str | None] = mapped_column(String(128))
    event_type: Mapped[str] = mapped_column(String(32))
    result_status: Mapped[str] = mapped_column(String(32))
    fail_reason: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(String(64))
    ip_location: Mapped[str | None] = mapped_column(String(255))
    device_type: Mapped[str | None] = mapped_column(String(32))
    os_name: Mapped[str | None] = mapped_column(String(64))
    browser_name: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(Text)
    trace_id: Mapped[str | None] = mapped_column(String(128))
    extra_data: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class IAMOperationLog(Base):
    __tablename__ = "iam_operation_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None]
    session_id: Mapped[str | None] = mapped_column(String(128))
    module_code: Mapped[str] = mapped_column(String(64))
    action_code: Mapped[str] = mapped_column(String(64))
    target_type: Mapped[str | None] = mapped_column(String(64))
    target_id: Mapped[str | None] = mapped_column(String(128))
    target_name: Mapped[str | None] = mapped_column(String(255))
    request_method: Mapped[str | None] = mapped_column(String(16))
    request_path: Mapped[str | None] = mapped_column(String(255))
    request_ip: Mapped[str | None] = mapped_column(String(64))
    request_payload: Mapped[dict | None] = mapped_column(JSON)
    response_payload: Mapped[dict | None] = mapped_column(JSON)
    operation_status: Mapped[str] = mapped_column(String(32))
    error_message: Mapped[str | None] = mapped_column(String(500))
    trace_id: Mapped[str | None] = mapped_column(String(128))
    operated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    extra_data: Mapped[dict | None] = mapped_column(JSON)


IamUserModel = IAMUser
IamUserIdentityModel = IAMUserIdentity
IamRoleModel = IAMRole
IamPermissionModel = IAMPermission
IamRolePermissionModel = IAMRolePermission
IamUserRoleModel = IAMUserRole
IamSessionModel = IAMSession
IamLoginLogModel = IAMLoginLog
IamOperationLogModel = IAMOperationLog
