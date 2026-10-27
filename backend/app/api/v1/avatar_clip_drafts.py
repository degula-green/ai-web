from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import FileResponse

from app.api.deps import get_avatar_clip_draft_service, get_clip_render_service, get_current_auth_context
from app.core.exceptions import ContractError
from app.core.response import ResponseEnvelope, success_response
from app.schemas.avatar_clip_draft import (
    AvatarClipDraftCreateRequest,
    AvatarClipDraftListResponse,
    AvatarClipDraftRead,
    AvatarClipDraftUpdateRequest,
)
from app.schemas.clip_render import ClipRenderRequest, ClipRenderResponse
from app.services.auth_service import AuthContext
from app.services.avatar_clip_draft_service import AvatarClipDraftService
from app.services.clip_render_service import ClipRenderService

router = APIRouter()


@router.post("", response_model=ResponseEnvelope[AvatarClipDraftRead])
def create_avatar_clip_draft(
    payload: AvatarClipDraftCreateRequest,
    context: AuthContext = Depends(get_current_auth_context),
    service: AvatarClipDraftService = Depends(get_avatar_clip_draft_service),
) -> ResponseEnvelope[AvatarClipDraftRead]:
    return success_response(service.create(user_id=context.user.id, payload=payload), message="avatar clip draft created")


@router.get("", response_model=ResponseEnvelope[AvatarClipDraftListResponse])
def list_avatar_clip_drafts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    context: AuthContext = Depends(get_current_auth_context),
    service: AvatarClipDraftService = Depends(get_avatar_clip_draft_service),
) -> ResponseEnvelope[AvatarClipDraftListResponse]:
    items = service.list_by_user(user_id=context.user.id, limit=limit, offset=offset)
    return success_response(AvatarClipDraftListResponse(items=items))


@router.get("/{draft_id}", response_model=ResponseEnvelope[AvatarClipDraftRead])
def get_avatar_clip_draft(
    draft_id: str,
    context: AuthContext = Depends(get_current_auth_context),
    service: AvatarClipDraftService = Depends(get_avatar_clip_draft_service),
) -> ResponseEnvelope[AvatarClipDraftRead]:
    return success_response(service.get(user_id=context.user.id, draft_id=draft_id))


@router.post("/{draft_id}/clip-render", response_model=ResponseEnvelope[ClipRenderResponse])
def clip_render_avatar_clip_draft(
    draft_id: str,
    payload: ClipRenderRequest = Body(default_factory=ClipRenderRequest),
    context: AuthContext = Depends(get_current_auth_context),
    service: AvatarClipDraftService = Depends(get_avatar_clip_draft_service),
    clip_service: ClipRenderService = Depends(get_clip_render_service),
) -> ResponseEnvelope[ClipRenderResponse]:
    service.get(user_id=context.user.id, draft_id=draft_id)
    data = clip_service.render_for_user(
        user_id=context.user.id,
        draft_id=draft_id,
        subtitle_segments=payload.segments,
        render_config=payload.render_config,
        playback_path=f"/api/v1/avatar-clip-drafts/{draft_id}/clipped-video",
    )
    service.sync_from_creation_draft_id(user_id=context.user.id, draft_id=draft_id)
    return success_response(data, message="avatar clip rendered")


@router.get("/{draft_id}/clipped-video")
def stream_avatar_clip_clipped_video(
    draft_id: str,
    context: AuthContext = Depends(get_current_auth_context),
    service: AvatarClipDraftService = Depends(get_avatar_clip_draft_service),
    clip_service: ClipRenderService = Depends(get_clip_render_service),
) -> FileResponse:
    service.get(user_id=context.user.id, draft_id=draft_id)
    path = clip_service.local_clipped_path(draft_id)
    if path is None:
        raise ContractError("local clipped video not found", status_code=404)
    return FileResponse(
        path,
        media_type="video/mp4",
        filename=f"{draft_id}_clipped.mp4",
    )


@router.patch("/{draft_id}", response_model=ResponseEnvelope[AvatarClipDraftRead])
def update_avatar_clip_draft(
    draft_id: str,
    payload: AvatarClipDraftUpdateRequest,
    context: AuthContext = Depends(get_current_auth_context),
    service: AvatarClipDraftService = Depends(get_avatar_clip_draft_service),
) -> ResponseEnvelope[AvatarClipDraftRead]:
    return success_response(service.update(user_id=context.user.id, draft_id=draft_id, payload=payload), message="avatar clip draft updated")


@router.delete("/{draft_id}", response_model=ResponseEnvelope[dict])
def delete_avatar_clip_draft(
    draft_id: str,
    context: AuthContext = Depends(get_current_auth_context),
    service: AvatarClipDraftService = Depends(get_avatar_clip_draft_service),
) -> ResponseEnvelope[dict]:
    service.delete(user_id=context.user.id, draft_id=draft_id)
    return success_response({"draft_id": draft_id}, message="avatar clip draft deleted")
