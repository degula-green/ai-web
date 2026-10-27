from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_avatar_model_draft_service, get_current_auth_context
from app.core.response import ResponseEnvelope, success_response
from app.schemas.avatar_model_draft import (
    AvatarModelDraftCreateRequest,
    AvatarModelDraftListResponse,
    AvatarModelDraftRead,
    AvatarModelDraftUpdateRequest,
)
from app.services.auth_service import AuthContext
from app.services.avatar_model_draft_service import AvatarModelDraftService

router = APIRouter()


@router.post("", response_model=ResponseEnvelope[AvatarModelDraftRead])
def create_avatar_model_draft(
    payload: AvatarModelDraftCreateRequest,
    context: AuthContext = Depends(get_current_auth_context),
    service: AvatarModelDraftService = Depends(get_avatar_model_draft_service),
) -> ResponseEnvelope[AvatarModelDraftRead]:
    return success_response(service.create(user_id=context.user.id, payload=payload), message="avatar model draft created")


@router.get("", response_model=ResponseEnvelope[AvatarModelDraftListResponse])
def list_avatar_model_drafts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    context: AuthContext = Depends(get_current_auth_context),
    service: AvatarModelDraftService = Depends(get_avatar_model_draft_service),
) -> ResponseEnvelope[AvatarModelDraftListResponse]:
    items = service.list_by_user(user_id=context.user.id, limit=limit, offset=offset)
    return success_response(AvatarModelDraftListResponse(items=items))


@router.get("/{draft_id}", response_model=ResponseEnvelope[AvatarModelDraftRead])
def get_avatar_model_draft(
    draft_id: str,
    context: AuthContext = Depends(get_current_auth_context),
    service: AvatarModelDraftService = Depends(get_avatar_model_draft_service),
) -> ResponseEnvelope[AvatarModelDraftRead]:
    return success_response(service.get(user_id=context.user.id, draft_id=draft_id))


@router.patch("/{draft_id}", response_model=ResponseEnvelope[AvatarModelDraftRead])
def update_avatar_model_draft(
    draft_id: str,
    payload: AvatarModelDraftUpdateRequest,
    context: AuthContext = Depends(get_current_auth_context),
    service: AvatarModelDraftService = Depends(get_avatar_model_draft_service),
) -> ResponseEnvelope[AvatarModelDraftRead]:
    return success_response(service.update(user_id=context.user.id, draft_id=draft_id, payload=payload), message="avatar model draft updated")


@router.delete("/{draft_id}", response_model=ResponseEnvelope[dict])
def delete_avatar_model_draft(
    draft_id: str,
    context: AuthContext = Depends(get_current_auth_context),
    service: AvatarModelDraftService = Depends(get_avatar_model_draft_service),
) -> ResponseEnvelope[dict]:
    service.delete(user_id=context.user.id, draft_id=draft_id)
    return success_response({"draft_id": draft_id}, message="avatar model draft deleted")
