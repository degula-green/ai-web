from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse

from app.api.deps import get_clip_render_service, get_current_auth_context, get_review_service
from app.core.exceptions import ContractError
from app.core.response import ResponseEnvelope, success_response
from app.schemas.review import ReviewClipVideoRequest, ReviewClipVideoResponse, ReviewPreviewRequest, ReviewResult
from app.services.auth_service import AuthContext
from app.services.clip_render_service import ClipRenderService
from app.services.review_service import ReviewService

router = APIRouter()


@router.post("/preview", response_model=ResponseEnvelope[ReviewResult])
def preview_review(
    payload: ReviewPreviewRequest,
    service: ReviewService = Depends(get_review_service),
) -> ResponseEnvelope[ReviewResult]:
    return success_response(service.preview(payload))


@router.post("/clip-video", response_model=ResponseEnvelope[ReviewClipVideoResponse])
def clip_review_video(
    payload: ReviewClipVideoRequest,
    clip_service: ClipRenderService = Depends(get_clip_render_service),
) -> ResponseEnvelope[ReviewClipVideoResponse]:
    data = clip_service.render_review_clip(
        user_id=None,
        media_url=payload.media_url,
        delete_segments=[segment.model_dump() for segment in payload.delete_segments],
    )
    return success_response(data, message="review clip created")


@router.post("/clip-video-upload", response_model=ResponseEnvelope[ReviewClipVideoResponse])
async def clip_review_video_upload(
    delete_segments: str = Form(default="[]"),
    source_file: UploadFile = File(...),
    clip_service: ClipRenderService = Depends(get_clip_render_service),
) -> ResponseEnvelope[ReviewClipVideoResponse]:
    try:
        parsed_segments = json.loads(delete_segments or "[]")
    except json.JSONDecodeError as exc:
        raise ContractError("delete_segments must be valid JSON", status_code=400) from exc
    if not isinstance(parsed_segments, list):
        raise ContractError("delete_segments must be a JSON array", status_code=400)

    suffix = Path(source_file.filename or "source.mp4").suffix or ".mp4"
    temp_fd, temp_name = tempfile.mkstemp(prefix="review_upload_", suffix=suffix)
    os.close(temp_fd)
    temp_path = Path(temp_name)
    try:
        temp_path.write_bytes(await source_file.read())
        data = clip_service.render_review_clip_upload(
            user_id=None,
            source_file_path=temp_path,
            delete_segments=parsed_segments,
        )
    finally:
        temp_path.unlink(missing_ok=True)

    return success_response(data, message="review clip created")


@router.post("/merge-avatar-video-upload", response_model=ResponseEnvelope[ReviewClipVideoResponse])
async def merge_review_avatar_video_upload(
    base_file: UploadFile = File(...),
    avatar_file: UploadFile = File(...),
    overlay_position: str = Form(default="bottom-right"),
    overlay_size_percent: float = Form(default=30),
    overlay_shape: str = Form(default="square"),
    clip_service: ClipRenderService = Depends(get_clip_render_service),
) -> ResponseEnvelope[ReviewClipVideoResponse]:
    base_suffix = Path(base_file.filename or "base.mp4").suffix or ".mp4"
    avatar_suffix = Path(avatar_file.filename or "avatar.mp4").suffix or ".mp4"
    base_fd, base_name = tempfile.mkstemp(prefix="review_merge_base_", suffix=base_suffix)
    avatar_fd, avatar_name = tempfile.mkstemp(prefix="review_merge_avatar_", suffix=avatar_suffix)
    os.close(base_fd)
    os.close(avatar_fd)
    base_path = Path(base_name)
    avatar_path = Path(avatar_name)
    try:
        base_path.write_bytes(await base_file.read())
        avatar_path.write_bytes(await avatar_file.read())
        data = clip_service.render_review_avatar_merge_upload(
            user_id=None,
            base_file_path=base_path,
            avatar_file_path=avatar_path,
            overlay_position=overlay_position,
            overlay_size_percent=overlay_size_percent,
            overlay_shape=overlay_shape,
        )
    finally:
        base_path.unlink(missing_ok=True)
        avatar_path.unlink(missing_ok=True)

    return success_response(data, message="review avatar merge created")


@router.get("/clip-video/{clip_id}")
def stream_review_clip_video(
    clip_id: str,
    clip_service: ClipRenderService = Depends(get_clip_render_service),
) -> FileResponse:
    path = clip_service.local_review_clip_path(user_id="", clip_id=clip_id)
    if path is None:
        raise ContractError("review clipped video not found", status_code=404)
    return FileResponse(
        path,
        media_type="video/mp4",
        filename=f"{clip_id}.mp4",
    )


@router.get("/clip-audio/{clip_id}")
def stream_review_clip_audio(
    clip_id: str,
    clip_service: ClipRenderService = Depends(get_clip_render_service),
) -> FileResponse:
    path = clip_service.local_review_clip_audio_path(user_id="", clip_id=clip_id)
    if path is None:
        raise ContractError("review clipped audio not found", status_code=404)
    return FileResponse(
        path,
        media_type="audio/mp4",
        filename=f"{clip_id}.m4a",
    )
