from __future__ import annotations

from datetime import datetime

from app.core.exceptions import ContractError
from app.db.models.iam import IAMPermission, IAMRole, IAMSession, IAMUser
from app.db.repositories.iam_repository import IAMRepository
from app.schemas.auth import PermissionBrief, RoleBrief
from app.schemas.iam import (
    AssignRolePermissionsResponseData,
    AssignUserRolesResponseData,
    ForceLogoutResponseData,
    PermissionListItem,
    RoleListItem,
    SessionListItem,
    UserListItem,
)
from app.services.auth_service import AuthContext


class IAMService:
    def __init__(self, *, repository: IAMRepository) -> None:
        self.repository = repository

    def list_users(self, *, context: AuthContext, keyword: str | None, status: str | None, user_type: str | None, role_code: str | None, page_no: int, page_size: int) -> dict:
        self._ensure_permission(context, "user:manage", "无权限访问用户列表")
        items, total = self.repository.list_users_public(keyword=keyword, status=status, user_type=user_type, role_code=role_code, page_no=page_no, page_size=page_size)
        return {"list": [self._to_user_list_item(item).model_dump() for item in items], "pageNo": page_no, "pageSize": page_size, "total": total}

    def list_roles(self, *, context: AuthContext, keyword: str | None, role_type: str | None, status: str | None, is_builtin: int | None, page_no: int, page_size: int) -> dict:
        self._ensure_permission(context, "role:manage", "无权限访问角色列表")
        items, total = self.repository.list_roles_public(keyword=keyword, role_type=role_type, status=status, is_builtin=is_builtin, page_no=page_no, page_size=page_size)
        return {"list": [self._to_role_list_item(item).model_dump() for item in items], "pageNo": page_no, "pageSize": page_size, "total": total}

    def list_permissions(self, *, context: AuthContext, keyword: str | None, module_code: str | None, action_code: str | None, permission_type: str | None, status: str | None, parent_id: int | None, page_no: int, page_size: int) -> dict:
        self._ensure_permission(context, "permission:manage", "无权限访问权限列表")
        items, total = self.repository.list_permissions_public(keyword=keyword, module_code=module_code, action_code=action_code, permission_type=permission_type, status=status, parent_id=parent_id, page_no=page_no, page_size=page_size)
        return {"list": [self._to_permission_list_item(item).model_dump() for item in items], "pageNo": page_no, "pageSize": page_size, "total": total}

    def assign_user_roles(self, *, context: AuthContext, user_id: int, role_ids: list[int], remark: str | None) -> AssignUserRolesResponseData:
        self._ensure_permission(context, "user:manage", "无权限分配用户角色")
        if not role_ids:
            raise ContractError("参数错误", status_code=400)
        if self.repository.get_user_by_id(user_id) is None:
            raise ContractError("用户不存在", status_code=404)
        roles = self.repository.get_roles_by_ids_public(role_ids)
        if len(roles) != len(set(role_ids)):
            raise ContractError("用户或角色不存在", status_code=404)
        if any(role.status != "active" for role in roles):
            raise ContractError("角色状态不可分配", status_code=409)
        assigned_roles = self.repository.assign_user_roles_public(user_id=user_id, role_ids=role_ids, assigned_by=context.user.id, remark=remark)
        return AssignUserRolesResponseData(
            userId=user_id,
            roleIds=[role.id for role in assigned_roles],
            roles=[RoleBrief(roleId=role.id, roleCode=role.role_code, roleName=role.role_name) for role in assigned_roles],
        )

    def assign_role_permissions(self, *, context: AuthContext, role_id: int, permission_ids: list[int], remark: str | None) -> AssignRolePermissionsResponseData:
        self._ensure_permission(context, "role:manage", "无权限分配角色权限")
        if not permission_ids:
            raise ContractError("参数错误", status_code=400)
        if not self.repository.get_roles_by_ids_public([role_id]):
            raise ContractError("角色不存在", status_code=404)
        permissions = self.repository.get_permissions_by_ids_public(permission_ids)
        if len(permissions) != len(set(permission_ids)):
            raise ContractError("角色或权限不存在", status_code=404)
        if any(permission.status != "active" for permission in permissions):
            raise ContractError("权限状态不可分配", status_code=409)
        assigned_permissions = self.repository.assign_role_permissions_public(role_id=role_id, permission_ids=permission_ids, granted_by=context.user.id, remark=remark)
        return AssignRolePermissionsResponseData(
            roleId=role_id,
            permissionIds=[permission.id for permission in assigned_permissions],
            permissions=[PermissionBrief(permissionId=permission.id, permissionCode=permission.permission_code, permissionName=permission.permission_name) for permission in assigned_permissions],
        )

    def list_sessions(self, *, context: AuthContext, user_id: int | None, login_type: str | None, device_type: str | None, session_status: str | None, page_no: int, page_size: int) -> dict:
        self._ensure_permission(context, "session:manage", "无权限访问会话列表")
        items, total = self.repository.list_sessions_public(user_id=user_id, login_type=login_type, device_type=device_type, session_status=session_status, page_no=page_no, page_size=page_size)
        return {"list": [self._to_session_list_item(item).model_dump() for item in items], "pageNo": page_no, "pageSize": page_size, "total": total}

    def force_logout(self, *, context: AuthContext, session_id: str, revoke_reason: str) -> ForceLogoutResponseData:
        self._ensure_permission(context, "session:manage", "无权限强制下线")
        iam_session = self.repository.get_session(session_id)
        if iam_session is None:
            raise ContractError("会话不存在", status_code=404)
        if iam_session.session_status != "active":
            raise ContractError("会话已失效", status_code=409)
        updated = self.repository.set_session_status(session_id=session_id, session_status="revoked", revoke_reason=revoke_reason)
        if updated is None:
            raise ContractError("会话不存在", status_code=404)
        return ForceLogoutResponseData(sessionId=updated.session_id, sessionStatus=updated.session_status, revokeReason=revoke_reason, logoutAt=self._fmt_dt(updated.logout_at))

    @staticmethod
    def _ensure_permission(context: AuthContext, permission_code: str, message: str) -> None:
        if permission_code not in {permission.permission_code for permission in context.permissions}:
            raise ContractError(message, status_code=403)

    def _to_user_list_item(self, user: IAMUser) -> UserListItem:
        roles = self.repository.get_roles_for_user(user.id)
        return UserListItem(
            id=user.id,
            userNo=user.user_no,
            username=user.username,
            nickname=user.nickname,
            realName=user.real_name,
            phone=user.phone,
            email=user.email,
            status=user.status,
            userType=user.user_type,
            lastLoginAt=self._fmt_dt(user.last_login_at),
            roles=[RoleBrief(roleId=role.id, roleCode=role.role_code, roleName=role.role_name) for role in roles],
        )

    @staticmethod
    def _to_role_list_item(role: IAMRole) -> RoleListItem:
        return RoleListItem(id=role.id, roleCode=role.role_code, roleName=role.role_name, roleType=role.role_type, status=role.status, sortOrder=role.sort_order, isBuiltin=1 if role.is_builtin else 0, description=role.description)

    @staticmethod
    def _to_permission_list_item(permission: IAMPermission) -> PermissionListItem:
        return PermissionListItem(id=permission.id, permissionCode=permission.permission_code, permissionName=permission.permission_name, moduleCode=permission.module_code, actionCode=permission.action_code, permissionType=permission.permission_type, parentId=permission.parent_id, path=permission.path, status=permission.status, sortOrder=permission.sort_order, isBuiltin=1 if permission.is_builtin else 0, description=permission.description)

    @staticmethod
    def _to_session_list_item(iam_session: IAMSession) -> SessionListItem:
        return SessionListItem(sessionId=iam_session.session_id, userId=iam_session.user_id, identityId=iam_session.identity_id, loginType=iam_session.login_type, deviceType=iam_session.device_type, deviceId=iam_session.device_id, clientVersion=iam_session.client_version, osName=iam_session.os_name, browserName=iam_session.browser_name, ipAddress=iam_session.ip_address, ipLocation=iam_session.ip_location, loginAt=IAMService._fmt_dt(iam_session.login_at), lastActiveAt=IAMService._fmt_dt(iam_session.last_active_at), expiredAt=IAMService._fmt_dt(iam_session.expired_at), logoutAt=IAMService._fmt_dt(iam_session.logout_at), sessionStatus=iam_session.session_status)

    @staticmethod
    def _fmt_dt(value: datetime | None) -> str | None:
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else None
