from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_avatar_draft_service, get_current_auth_context
from app.core.response import ResponseEnvelope, success_response
from app.schemas.avatar_draft import AvatarDraftListResponse, AvatarDraftRead
from app.services.auth_service import AuthContext
from app.services.avatar_draft_service import AvatarDraftService

router = APIRouter()


@router.get("", response_model=ResponseEnvelope[AvatarDraftListResponse])
def list_avatar_drafts(
    scene: str | None = Query(default=None, alias="scene"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    context: AuthContext = Depends(get_current_auth_context),
    service: AvatarDraftService = Depends(get_avatar_draft_service),
) -> ResponseEnvelope[AvatarDraftListResponse]:
    items = service.list_by_user(user_id=context.user.id, scene_code=scene, limit=limit, offset=offset)
    return success_response(AvatarDraftListResponse(items=items))


@router.get("/{draft_id}", response_model=ResponseEnvelope[AvatarDraftRead])
def get_avatar_draft(
    draft_id: str,
    context: AuthContext = Depends(get_current_auth_context),
    service: AvatarDraftService = Depends(get_avatar_draft_service),
) -> ResponseEnvelope[AvatarDraftRead]:
    return success_response(service.get(user_id=context.user.id, draft_id=draft_id))
