from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_auth_context, get_iam_service
from app.core.contract import contract_success
from app.schemas.iam import AssignRolePermissionsRequest, AssignUserRolesRequest, ForceLogoutRequest

router = APIRouter()


@router.get("/users")
def list_users(
    keyword: str | None = None,
    status: str | None = None,
    userType: str | None = None,
    roleCode: str | None = None,
    pageNo: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    iam_service=Depends(get_iam_service),
    context=Depends(get_current_auth_context),
):
    data = iam_service.list_users(context=context, keyword=keyword, status=status, user_type=userType, role_code=roleCode, page_no=pageNo, page_size=pageSize)
    return contract_success(data, msg="查询成功")


@router.get("/roles")
def list_roles(
    keyword: str | None = None,
    roleType: str | None = None,
    status: str | None = None,
    isBuiltin: int | None = Query(default=None, ge=0, le=1),
    pageNo: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    iam_service=Depends(get_iam_service),
    context=Depends(get_current_auth_context),
):
    data = iam_service.list_roles(context=context, keyword=keyword, role_type=roleType, status=status, is_builtin=isBuiltin, page_no=pageNo, page_size=pageSize)
    return contract_success(data, msg="查询成功")


@router.get("/permissions")
def list_permissions(
    keyword: str | None = None,
    moduleCode: str | None = None,
    actionCode: str | None = None,
    permissionType: str | None = None,
    status: str | None = None,
    parentId: int | None = None,
    pageNo: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    iam_service=Depends(get_iam_service),
    context=Depends(get_current_auth_context),
):
    data = iam_service.list_permissions(context=context, keyword=keyword, module_code=moduleCode, action_code=actionCode, permission_type=permissionType, status=status, parent_id=parentId, page_no=pageNo, page_size=pageSize)
    return contract_success(data, msg="查询成功")


@router.put("/users/{userId}/roles")
def assign_user_roles(userId: int, payload: AssignUserRolesRequest, iam_service=Depends(get_iam_service), context=Depends(get_current_auth_context)):
    data = iam_service.assign_user_roles(context=context, user_id=userId, role_ids=payload.roleIds, remark=payload.remark)
    return contract_success(data.model_dump(), msg="分配成功")


@router.put("/roles/{roleId}/permissions")
def assign_role_permissions(roleId: int, payload: AssignRolePermissionsRequest, iam_service=Depends(get_iam_service), context=Depends(get_current_auth_context)):
    data = iam_service.assign_role_permissions(context=context, role_id=roleId, permission_ids=payload.permissionIds, remark=payload.remark)
    return contract_success(data.model_dump(), msg="授权成功")


@router.get("/sessions")
def list_sessions(
    userId: int | None = None,
    loginType: str | None = None,
    deviceType: str | None = None,
    sessionStatus: str | None = None,
    pageNo: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    iam_service=Depends(get_iam_service),
    context=Depends(get_current_auth_context),
):
    data = iam_service.list_sessions(context=context, user_id=userId, login_type=loginType, device_type=deviceType, session_status=sessionStatus, page_no=pageNo, page_size=pageSize)
    return contract_success(data, msg="查询成功")


@router.post("/sessions/force-logout")
def force_logout(payload: ForceLogoutRequest, iam_service=Depends(get_iam_service), context=Depends(get_current_auth_context)):
    data = iam_service.force_logout(context=context, session_id=payload.sessionId, revoke_reason=payload.revokeReason)
    return contract_success(data.model_dump(), msg="强制下线成功")
