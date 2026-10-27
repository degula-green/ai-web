from __future__ import annotations

from pydantic import BaseModel

from app.schemas.auth import PermissionBrief, RoleBrief


class UserListItem(BaseModel):
    id: int
    userNo: str
    username: str | None = None
    nickname: str
    realName: str | None = None
    phone: str | None = None
    email: str | None = None
    status: str
    userType: str
    lastLoginAt: str | None = None
    roles: list[RoleBrief]


class UserListData(BaseModel):
    list: list[UserListItem]
    pageNo: int
    pageSize: int
    total: int


class RoleListItem(BaseModel):
    id: int
    roleCode: str
    roleName: str
    roleType: str
    status: str
    sortOrder: int
    isBuiltin: int
    description: str | None = None


class RoleListData(BaseModel):
    list: list[RoleListItem]
    pageNo: int
    pageSize: int
    total: int


class PermissionListItem(BaseModel):
    id: int
    permissionCode: str
    permissionName: str
    moduleCode: str
    actionCode: str
    permissionType: str
    parentId: int | None = None
    path: str | None = None
    status: str
    sortOrder: int
    isBuiltin: int
    description: str | None = None


class PermissionListData(BaseModel):
    list: list[PermissionListItem]
    pageNo: int
    pageSize: int
    total: int


class SessionListItem(BaseModel):
    sessionId: str
    userId: int
    identityId: int
    loginType: str
    deviceType: str
    deviceId: str | None = None
    clientVersion: str | None = None
    osName: str | None = None
    browserName: str | None = None
    ipAddress: str | None = None
    ipLocation: str | None = None
    loginAt: str | None = None
    lastActiveAt: str | None = None
    expiredAt: str | None = None
    logoutAt: str | None = None
    sessionStatus: str


class SessionListData(BaseModel):
    list: list[SessionListItem]
    pageNo: int
    pageSize: int
    total: int


class AssignUserRolesRequest(BaseModel):
    roleIds: list[int]
    remark: str | None = None


class AssignUserRolesResponseData(BaseModel):
    userId: int
    roleIds: list[int]
    roles: list[RoleBrief]


class AssignRolePermissionsRequest(BaseModel):
    permissionIds: list[int]
    remark: str | None = None


class AssignRolePermissionsResponseData(BaseModel):
    roleId: int
    permissionIds: list[int]
    permissions: list[PermissionBrief]


class ForceLogoutRequest(BaseModel):
    sessionId: str
    revokeReason: str


class ForceLogoutResponseData(BaseModel):
    sessionId: str
    sessionStatus: str
    revokeReason: str
    logoutAt: str | None = None


AssignUserRolesData = AssignUserRolesResponseData
AssignRolePermissionsData = AssignRolePermissionsResponseData
ForceLogoutData = ForceLogoutResponseData
