from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import generate_salt, hash_password
from app.db.models.iam import IAMPermission, IAMRole, IAMRolePermission, IAMSession, IAMUser, IAMUserIdentity, IAMUserRole


@dataclass(slots=True)
class PaginationResult:
    items: list
    total: int
    page_no: int
    page_size: int


class IAMRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    @contextmanager
    def session_scope(self):
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def ensure_seed_data(self, *, bootstrap_password: str, password_hash_iterations: int, session_ttl_seconds: int) -> None:
        now = datetime.utcnow()
        required_permissions = [
            ("user:manage", "用户管理", "user", "manage", "/api/v1/iam/users", 1, "用户管理相关权限"),
            ("role:manage", "角色管理", "role", "manage", "/api/v1/iam/roles", 2, "角色管理相关权限"),
            ("permission:manage", "权限管理", "permission", "manage", "/api/v1/iam/permissions", 3, "权限管理相关权限"),
            ("session:manage", "会话管理", "session", "manage", "/api/v1/iam/sessions", 4, "会话管理相关权限"),
            ("task:create", "创建任务", "task", "create", "/api/v1/tasks", 5, "创建任务"),
            ("review:approve", "审核通过", "review", "approve", "/api/v1/review", 6, "审核通过"),
            ("workflow:publish", "发布工作流", "workflow", "publish", "/api/v1/workflows", 7, "发布工作流"),
            ("platform_account:manage", "平台账号管理", "platform_account", "manage", "/api/v1/platform", 8, "平台账号管理"),
        ]

        with self.session_scope() as session:
            for permission_code, permission_name, module_code, action_code, path, sort_order, description in required_permissions:
                permission = session.scalar(select(IAMPermission).where(IAMPermission.permission_code == permission_code, IAMPermission.is_deleted.is_(False)))
                if permission is None:
                    session.add(
                        IAMPermission(
                            permission_code=permission_code,
                            permission_name=permission_name,
                            module_code=module_code,
                            action_code=action_code,
                            permission_type="api",
                            parent_id=None,
                            path=path,
                            status="active",
                            sort_order=sort_order,
                            description=description,
                            is_builtin=True,
                            is_deleted=False,
                            created_by=0,
                            updated_by=0,
                        )
                    )

            session.flush()

            # Ensure 'normal' role exists
            normal_role = session.scalar(select(IAMRole).where(IAMRole.role_code == "normal", IAMRole.is_deleted.is_(False)))
            if normal_role is None:
                session.add(
                    IAMRole(
                        role_code="normal",
                        role_name="普通用户",
                        role_type="system",
                        status="active",
                        sort_order=10,
                        description="注册用户的默认角色",
                        is_builtin=True,
                        is_deleted=False,
                        created_by=0,
                        updated_by=0,
                    )
                )
            
            session.flush()
            
            # Assign base permissions to 'normal' role so users can navigate and view these pages
            normal_role = session.scalar(select(IAMRole).where(IAMRole.role_code == "normal", IAMRole.is_deleted.is_(False)))
            if normal_role is not None:
                # Grant access to review and workflow features for the demo/standard user
                permission_codes = ["review:approve", "workflow:publish"]
                for p_code in permission_codes:
                    permission_id = session.scalar(select(IAMPermission.id).where(IAMPermission.permission_code == p_code, IAMPermission.status == "active"))
                    if permission_id:
                        exists = session.scalar(select(IAMRolePermission).where(IAMRolePermission.role_id == normal_role.id, IAMRolePermission.permission_id == permission_id))
                        if not exists:
                            session.add(IAMRolePermission(role_id=normal_role.id, permission_id=permission_id, granted_by=0, status="active", remark="bootstrap_default"))


            for identity in session.scalars(select(IAMUserIdentity).where(IAMUserIdentity.identity_type.in_(["username", "phone", "email"]), IAMUserIdentity.is_enabled.is_(True))):
                if identity.credential_hash and len(identity.credential_hash) == 64 and identity.credential_salt:
                    continue
                salt = generate_salt()
                identity.credential_salt = salt
                identity.credential_hash = hash_password(bootstrap_password, salt, password_hash_iterations)

            super_admin_role = session.scalar(select(IAMRole).where(IAMRole.role_code == "super_admin", IAMRole.is_deleted.is_(False)))
            if super_admin_role is not None:
                permission_ids = session.scalars(select(IAMPermission.id).where(IAMPermission.status == "active", IAMPermission.is_deleted.is_(False))).all()
                existing_ids = set(session.scalars(select(IAMRolePermission.permission_id).where(IAMRolePermission.role_id == super_admin_role.id, IAMRolePermission.status == "active")).all())
                for permission_id in permission_ids:
                    if permission_id in existing_ids:
                        continue
                    session.add(IAMRolePermission(role_id=super_admin_role.id, permission_id=permission_id, granted_by=1, status="active", remark="bootstrap"))

            for iam_session in session.scalars(select(IAMSession)):
                if iam_session.expired_at is None:
                    iam_session.expired_at = now + timedelta(seconds=session_ttl_seconds)

    def get_identity(self, identity_type: str, identity_key: str) -> IAMUserIdentity | None:
        with self.session_scope() as session:
            return session.scalar(select(IAMUserIdentity).where(IAMUserIdentity.identity_type == identity_type, IAMUserIdentity.identity_key == identity_key))

    def get_user(self, user_id: int) -> IAMUser | None:
        with self.session_scope() as session:
            return session.get(IAMUser, user_id)

    def get_user_by_id(self, user_id: int) -> IAMUser | None:
        return self.get_user(user_id)

    def get_roles_for_user(self, user_id: int) -> list[IAMRole]:
        with self.session_scope() as session:
            return list(
                session.scalars(
                    select(IAMRole)
                    .join(IAMUserRole, IAMUserRole.role_id == IAMRole.id)
                    .where(IAMUserRole.user_id == user_id, IAMUserRole.status == "active", IAMRole.status == "active", IAMRole.is_deleted.is_(False))
                    .order_by(IAMRole.sort_order.asc(), IAMRole.id.asc())
                ).all()
            )

    def get_permissions_for_user(self, user_id: int) -> list[IAMPermission]:
        with self.session_scope() as session:
            return list(
                session.scalars(
                    select(IAMPermission)
                    .join(IAMRolePermission, IAMRolePermission.permission_id == IAMPermission.id)
                    .join(IAMUserRole, IAMUserRole.role_id == IAMRolePermission.role_id)
                    .where(IAMUserRole.user_id == user_id, IAMUserRole.status == "active", IAMRolePermission.status == "active", IAMPermission.status == "active", IAMPermission.is_deleted.is_(False))
                    .distinct()
                    .order_by(IAMPermission.sort_order.asc(), IAMPermission.id.asc())
                ).all()
            )

    def touch_user_login(self, *, user_id: int, ip_address: str | None) -> None:
        with self.session_scope() as session:
            user = session.get(IAMUser, user_id)
            if user is not None:
                user.last_login_at = datetime.utcnow()
                user.last_login_ip = ip_address

    def upsert_session(self, *, session_id: str, user_id: int, identity_id: int, login_type: str, access_token_digest: str, refresh_token_digest: str, device_type: str, device_id: str | None, client_version: str | None, os_name: str | None, browser_name: str | None, ip_address: str | None, user_agent: str | None, expired_at: datetime, ip_location: str | None = "本地开发环境") -> IAMSession:
        with self.session_scope() as session:
            existing = session.scalar(select(IAMSession).where(IAMSession.session_id == session_id))
            if existing is None:
                existing = IAMSession(session_id=session_id, user_id=user_id, identity_id=identity_id, login_type=login_type, device_type=device_type, session_status="active", login_at=datetime.utcnow())
                session.add(existing)
            existing.access_token_digest = access_token_digest
            existing.refresh_token_digest = refresh_token_digest
            existing.device_type = device_type
            existing.device_id = device_id
            existing.client_version = client_version
            existing.os_name = os_name
            existing.browser_name = browser_name
            existing.ip_address = ip_address
            existing.ip_location = ip_location
            existing.user_agent = user_agent
            existing.last_active_at = datetime.utcnow()
            existing.expired_at = expired_at
            existing.logout_at = None
            existing.revoke_reason = None
            existing.session_status = "active"
            session.flush()
            session.refresh(existing)
            return existing

    def get_session(self, session_id: str) -> IAMSession | None:
        with self.session_scope() as session:
            return session.scalar(select(IAMSession).where(IAMSession.session_id == session_id))

    def update_session_tokens(self, *, session_id: str, access_token_digest: str, refresh_token_digest: str, expired_at: datetime) -> IAMSession | None:
        with self.session_scope() as session:
            iam_session = session.scalar(select(IAMSession).where(IAMSession.session_id == session_id))
            if iam_session is None:
                return None
            iam_session.access_token_digest = access_token_digest
            iam_session.refresh_token_digest = refresh_token_digest
            iam_session.expired_at = expired_at
            iam_session.last_active_at = datetime.utcnow()
            session.flush()
            session.refresh(iam_session)
            return iam_session

    def set_session_status(self, *, session_id: str, session_status: str, revoke_reason: str | None = None) -> IAMSession | None:
        with self.session_scope() as session:
            iam_session = session.scalar(select(IAMSession).where(IAMSession.session_id == session_id))
            if iam_session is None:
                return None
            iam_session.session_status = session_status
            iam_session.revoke_reason = revoke_reason
            iam_session.logout_at = datetime.utcnow()
            iam_session.last_active_at = datetime.utcnow()
            session.flush()
            session.refresh(iam_session)
            return iam_session

    def list_users(self, *, keyword: str | None, status: str | None, user_type: str | None, role_code: str | None, page_no: int, page_size: int) -> PaginationResult:
        with self.session_scope() as session:
            query = select(IAMUser).where(IAMUser.is_deleted.is_(False))
            if keyword:
                pattern = f"%{keyword}%"
                query = query.where(or_(IAMUser.username.like(pattern), IAMUser.nickname.like(pattern), IAMUser.real_name.like(pattern), IAMUser.phone.like(pattern), IAMUser.email.like(pattern)))
            if status:
                query = query.where(IAMUser.status == status)
            if user_type:
                query = query.where(IAMUser.user_type == user_type)
            if role_code:
                query = query.join(IAMUserRole, IAMUserRole.user_id == IAMUser.id).join(IAMRole, IAMRole.id == IAMUserRole.role_id).where(IAMUserRole.status == "active", IAMRole.role_code == role_code, IAMRole.is_deleted.is_(False))
            total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
            items = session.scalars(query.order_by(IAMUser.id.asc()).offset((page_no - 1) * page_size).limit(page_size)).all()
            return PaginationResult(list(items), int(total), page_no, page_size)

    def list_users_public(self, **kwargs) -> tuple[list[IAMUser], int]:
        res = self.list_users(**kwargs)
        return res.items, res.total

    def list_roles(self, *, keyword: str | None, role_type: str | None, status: str | None, is_builtin: int | None, page_no: int, page_size: int) -> PaginationResult:
        with self.session_scope() as session:
            query = select(IAMRole).where(IAMRole.is_deleted.is_(False))
            if keyword:
                pattern = f"%{keyword}%"
                query = query.where(or_(IAMRole.role_code.like(pattern), IAMRole.role_name.like(pattern)))
            if role_type:
                query = query.where(IAMRole.role_type == role_type)
            if status:
                query = query.where(IAMRole.status == status)
            if is_builtin is not None:
                query = query.where(IAMRole.is_builtin == bool(is_builtin))
            total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
            items = session.scalars(query.order_by(IAMRole.sort_order.asc(), IAMRole.id.asc()).offset((page_no - 1) * page_size).limit(page_size)).all()
            return PaginationResult(list(items), int(total), page_no, page_size)

    def list_roles_public(self, **kwargs) -> tuple[list[IAMRole], int]:
        res = self.list_roles(**kwargs)
        return res.items, res.total

    def list_permissions(self, *, keyword: str | None, module_code: str | None, action_code: str | None, permission_type: str | None, status: str | None, parent_id: int | None, page_no: int, page_size: int) -> PaginationResult:
        with self.session_scope() as session:
            query = select(IAMPermission).where(IAMPermission.is_deleted.is_(False))
            if keyword:
                pattern = f"%{keyword}%"
                query = query.where(or_(IAMPermission.permission_code.like(pattern), IAMPermission.permission_name.like(pattern)))
            if module_code:
                query = query.where(IAMPermission.module_code == module_code)
            if action_code:
                query = query.where(IAMPermission.action_code == action_code)
            if permission_type:
                query = query.where(IAMPermission.permission_type == permission_type)
            if status:
                query = query.where(IAMPermission.status == status)
            if parent_id is not None:
                query = query.where(IAMPermission.parent_id == parent_id)
            total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
            items = session.scalars(query.order_by(IAMPermission.sort_order.asc(), IAMPermission.id.asc()).offset((page_no - 1) * page_size).limit(page_size)).all()
            return PaginationResult(list(items), int(total), page_no, page_size)

    def list_permissions_public(self, **kwargs) -> tuple[list[IAMPermission], int]:
        res = self.list_permissions(**kwargs)
        return res.items, res.total

    def assign_user_roles(self, *, user_id: int, role_ids: list[int], assigned_by: int, remark: str | None) -> list[IAMRole]:
        with self.session_scope() as session:
            session.execute(delete(IAMUserRole).where(IAMUserRole.user_id == user_id))
            for role_id in role_ids:
                session.add(IAMUserRole(user_id=user_id, role_id=role_id, assigned_by=assigned_by, status="active", remark=remark))
            session.flush()
            return list(session.scalars(select(IAMRole).where(IAMRole.id.in_(role_ids))).all()) if role_ids else []

    def assign_role_permissions(self, *, role_id: int, permission_ids: list[int], granted_by: int, remark: str | None) -> list[IAMPermission]:
        with self.session_scope() as session:
            session.execute(delete(IAMRolePermission).where(IAMRolePermission.role_id == role_id))
            for permission_id in permission_ids:
                session.add(IAMRolePermission(role_id=role_id, permission_id=permission_id, granted_by=granted_by, status="active", remark=remark))
            session.flush()
            return list(session.scalars(select(IAMPermission).where(IAMPermission.id.in_(permission_ids))).all()) if permission_ids else []

    def assign_user_roles_public(self, **kwargs) -> list[IAMRole]:
        return self.assign_user_roles(**kwargs)

    def assign_role_permissions_public(self, **kwargs) -> list[IAMPermission]:
        return self.assign_role_permissions(**kwargs)

    def list_sessions_public(self, **kwargs) -> tuple[list[IAMSession], int]:
        res = self.list_sessions(**kwargs)
        return res.items, res.total

    def get_roles_by_ids_public(self, role_ids: list[int]) -> list[IAMRole]:
        return self.get_roles_by_ids(role_ids)

    def get_permissions_by_ids_public(self, permission_ids: list[int]) -> list[IAMPermission]:
        return self.get_permissions_by_ids(permission_ids)

    def list_sessions(self, *, user_id: int | None, login_type: str | None, device_type: str | None, session_status: str | None, page_no: int, page_size: int) -> PaginationResult:
        with self.session_scope() as session:
            query = select(IAMSession)
            if user_id is not None:
                query = query.where(IAMSession.user_id == user_id)
            if login_type:
                query = query.where(IAMSession.login_type == login_type)
            if device_type:
                query = query.where(IAMSession.device_type == device_type)
            if session_status:
                query = query.where(IAMSession.session_status == session_status)
            total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
            items = session.scalars(query.order_by(IAMSession.login_at.desc(), IAMSession.id.desc()).offset((page_no - 1) * page_size).limit(page_size)).all()
            return PaginationResult(list(items), int(total), page_no, page_size)

    def get_roles_by_ids(self, role_ids: list[int]) -> list[IAMRole]:
        if not role_ids:
            return []
        with self.session_scope() as session:
            return list(session.scalars(select(IAMRole).where(IAMRole.id.in_(role_ids), IAMRole.is_deleted.is_(False))).all())

    def get_permissions_by_ids(self, permission_ids: list[int]) -> list[IAMPermission]:
        if not permission_ids:
            return []
        with self.session_scope() as session:
            return list(session.scalars(select(IAMPermission).where(IAMPermission.id.in_(permission_ids), IAMPermission.is_deleted.is_(False))).all())


IamRepository = IAMRepository
