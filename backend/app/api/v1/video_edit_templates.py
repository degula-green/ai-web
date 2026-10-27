from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_auth_context, get_video_edit_template_service
from app.core.response import ResponseEnvelope, success_response
from app.schemas.video_edit_template import (
    VideoEditTemplateCreateRequest,
    VideoEditTemplateListResponse,
    VideoEditTemplateRead,
    VideoEditTemplateUpdateRequest,
)
from app.services.auth_service import AuthContext
from app.services.video_edit_template_service import VideoEditTemplateService

router = APIRouter()


@router.get("", response_model=ResponseEnvelope[VideoEditTemplateListResponse])
def list_video_edit_templates(
    template_type: str | None = Query(default="clip"),
    scene_code: str | None = Query(default=None),
    context: AuthContext = Depends(get_current_auth_context),
    service: VideoEditTemplateService = Depends(get_video_edit_template_service),
) -> ResponseEnvelope[VideoEditTemplateListResponse]:
    data = service.list_available(user_id=context.user.id, template_type=template_type, scene_code=scene_code)
    return success_response(data)


@router.post("", response_model=ResponseEnvelope[VideoEditTemplateRead])
def create_video_edit_template(
    payload: VideoEditTemplateCreateRequest,
    context: AuthContext = Depends(get_current_auth_context),
    service: VideoEditTemplateService = Depends(get_video_edit_template_service),
) -> ResponseEnvelope[VideoEditTemplateRead]:
    data = service.create_user_template(user_id=context.user.id, payload=payload)
    return success_response(data, message="video edit template created")


@router.patch("/{template_id}", response_model=ResponseEnvelope[VideoEditTemplateRead])
def update_video_edit_template(
    template_id: int,
    payload: VideoEditTemplateUpdateRequest,
    context: AuthContext = Depends(get_current_auth_context),
    service: VideoEditTemplateService = Depends(get_video_edit_template_service),
) -> ResponseEnvelope[VideoEditTemplateRead]:
    data = service.update_user_template(user_id=context.user.id, template_id=template_id, payload=payload)
    return success_response(data, message="video edit template updated")


@router.delete("/{template_id}", response_model=ResponseEnvelope[dict])
def delete_video_edit_template(
    template_id: int,
    context: AuthContext = Depends(get_current_auth_context),
    service: VideoEditTemplateService = Depends(get_video_edit_template_service),
) -> ResponseEnvelope[dict]:
    service.delete_user_template(user_id=context.user.id, template_id=template_id)
    return success_response({"template_id": template_id}, message="video edit template deleted")
