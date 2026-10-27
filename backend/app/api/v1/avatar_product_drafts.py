from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import FileResponse

from app.api.deps import (
    get_ai_model_service,
    get_avatar_product_clip_render_service,
    get_avatar_product_draft_service,
    get_current_auth_context,
)
from app.core.exceptions import ContractError
from app.core.response import ResponseEnvelope, success_response
from app.schemas.avatar_product_draft import (
    AvatarProductDraftCreateRequest,
    AvatarProductInstructionGenerateRequest,
    AvatarProductInstructionGenerateResponse,
    AvatarProductDraftListResponse,
    AvatarProductDraftRead,
    AvatarProductDraftUpdateRequest,
)
from app.schemas.clip_render import ClipRenderRequest, ClipRenderResponse
from app.schemas.creation_draft import DigitalHumanAssetUpdateRequest
from app.services.ai_model_service import AIModelService
from app.services.auth_service import AuthContext
from app.services.avatar_product_draft_service import AvatarProductDraftService
from app.services.clip_render_service import ClipRenderService

router = APIRouter()


@router.post("", response_model=ResponseEnvelope[AvatarProductDraftRead])
def create_avatar_product_draft(
    payload: AvatarProductDraftCreateRequest,
    context: AuthContext = Depends(get_current_auth_context),
    service: AvatarProductDraftService = Depends(get_avatar_product_draft_service),
) -> ResponseEnvelope[AvatarProductDraftRead]:
    return success_response(service.create(user_id=context.user.id, payload=payload), message="avatar product draft created")


@router.get("", response_model=ResponseEnvelope[AvatarProductDraftListResponse])
def list_avatar_product_drafts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    context: AuthContext = Depends(get_current_auth_context),
    service: AvatarProductDraftService = Depends(get_avatar_product_draft_service),
) -> ResponseEnvelope[AvatarProductDraftListResponse]:
    items = service.list_by_user(user_id=context.user.id, limit=limit, offset=offset)
    return success_response(AvatarProductDraftListResponse(items=items))


@router.get("/{draft_id}", response_model=ResponseEnvelope[AvatarProductDraftRead])
def get_avatar_product_draft(
    draft_id: str,
    context: AuthContext = Depends(get_current_auth_context),
    service: AvatarProductDraftService = Depends(get_avatar_product_draft_service),
) -> ResponseEnvelope[AvatarProductDraftRead]:
    return success_response(service.get(user_id=context.user.id, draft_id=draft_id))


@router.post("/{draft_id}/clip-render", response_model=ResponseEnvelope[ClipRenderResponse])
def clip_render_avatar_product_draft(
    draft_id: str,
    payload: ClipRenderRequest = Body(default_factory=ClipRenderRequest),
    context: AuthContext = Depends(get_current_auth_context),
    clip_service: ClipRenderService = Depends(get_avatar_product_clip_render_service),
) -> ResponseEnvelope[ClipRenderResponse]:
    data = clip_service.render_for_user(
        user_id=context.user.id,
        draft_id=draft_id,
        subtitle_segments=payload.segments,
        render_config=payload.render_config,
    )
    return success_response(data, message="avatar product clip rendered")


@router.get("/{draft_id}/clipped-video")
def stream_avatar_sales_clipped_video(
    draft_id: str,
    context: AuthContext = Depends(get_current_auth_context),
    draft_service: AvatarProductDraftService = Depends(get_avatar_product_draft_service),
    clip_service: ClipRenderService = Depends(get_avatar_product_clip_render_service),
) -> FileResponse:
    draft_service.get(user_id=context.user.id, draft_id=draft_id)
    path = clip_service.local_clipped_path(draft_id)
    if path is None:
        raise ContractError("鏈湴鍓緫鎴愮墖涓嶅瓨鍦紝璇峰厛鎵ц鍓緫", status_code=404)
    return FileResponse(
        path,
        media_type="video/mp4",
        filename=f"{draft_id}_clipped.mp4",
    )


@router.patch("/{draft_id}", response_model=ResponseEnvelope[AvatarProductDraftRead])
def update_avatar_product_draft(
    draft_id: str,
    payload: AvatarProductDraftUpdateRequest,
    context: AuthContext = Depends(get_current_auth_context),
    service: AvatarProductDraftService = Depends(get_avatar_product_draft_service),
) -> ResponseEnvelope[AvatarProductDraftRead]:
    return success_response(service.update(user_id=context.user.id, draft_id=draft_id, payload=payload), message="avatar product draft updated")


@router.post("/{draft_id}/auto-instruction", response_model=ResponseEnvelope[AvatarProductInstructionGenerateResponse])
def generate_avatar_product_instruction(
    draft_id: str,
    payload: AvatarProductInstructionGenerateRequest,
    context: AuthContext = Depends(get_current_auth_context),
    service: AvatarProductDraftService = Depends(get_avatar_product_draft_service),
    ai_model_service: AIModelService = Depends(get_ai_model_service),
) -> ResponseEnvelope[AvatarProductInstructionGenerateResponse]:
    data = service.generate_auto_instruction(
        user_id=context.user.id,
        draft_id=draft_id,
        image_urls=payload.image_urls,
        product_name=payload.product_name,
        ai_model_service=ai_model_service,
    )
    return success_response(data, message="avatar product instruction generated")


@router.post("/{draft_id}/digital-human-asset", response_model=ResponseEnvelope[AvatarProductDraftRead])
def update_avatar_product_draft_digital_human_asset(
    draft_id: str,
    payload: DigitalHumanAssetUpdateRequest,
    context: AuthContext = Depends(get_current_auth_context),
    service: AvatarProductDraftService = Depends(get_avatar_product_draft_service),
) -> ResponseEnvelope[AvatarProductDraftRead]:
    return success_response(
        service.update_digital_human_asset(user_id=context.user.id, draft_id=draft_id, payload=payload),
        message="avatar product digital human asset updated",
    )


@router.delete("/{draft_id}", response_model=ResponseEnvelope[dict])
def delete_avatar_product_draft(
    draft_id: str,
    context: AuthContext = Depends(get_current_auth_context),
    service: AvatarProductDraftService = Depends(get_avatar_product_draft_service),
) -> ResponseEnvelope[dict]:
    service.delete(user_id=context.user.id, draft_id=draft_id)
    return success_response({"draft_id": draft_id}, message="avatar product draft deleted")

