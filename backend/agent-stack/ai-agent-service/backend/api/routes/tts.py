# -*- coding: utf-8 -*-
"""
TTS / voice APIs.

Endpoints:
- GET    /api/v1/tts/voices
- POST   /api/v1/tts/voices/design
- POST   /api/v1/tts/voices/clone
- GET    /api/v1/tts/voices/{voice_id}
- DELETE /api/v1/tts/voices/{voice_id}
- POST   /api/v1/tts/generate
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from api.dependencies import get_current_user, get_current_user_optional
from services.main_auth_adapter import User
from services.tts_service import DashScopeTTSAPIError, TTSServiceError, tts_service
from utils.logger import logger

router = APIRouter()


def _to_absolute_urls(request: Request, payload: Any) -> Any:
    if isinstance(payload, dict):
        result = {}
        for key, value in payload.items():
            if key.endswith("_url") and isinstance(value, str) and value.startswith("/"):
                result[key] = tts_service.build_absolute_url(str(request.base_url).rstrip("/"), value)
            else:
                result[key] = _to_absolute_urls(request, value)
        return result
    if isinstance(payload, list):
        return [_to_absolute_urls(request, item) for item in payload]
    return payload


class VoiceCloneRequest(BaseModel):
    target_model: str = Field(..., description="驱动音色的语音合成模型，必须与后续TTS模型一致")
    prefix: str = Field(..., min_length=1, max_length=10, description="音色前缀，仅允许数字和字母，建议 10 字符内")
    audio_url: str = Field(..., description="公网可访问的参考音频 URL")
    language: Optional[str] = Field(default="zh", description="样本音频语言提示")
    max_prompt_audio_length: Optional[float] = Field(default=None, ge=3.0, le=30.0)
    enable_preprocess: Optional[bool] = None
    enrollment_config_name: str = Field(default=tts_service.DEFAULT_ENROLLMENT_CONFIG_NAME)


class VoiceDesignRequest(BaseModel):
    target_model: str = Field(..., description="驱动音色的语音合成模型，必须与后续TTS模型一致")
    prefix: str = Field(..., min_length=1, max_length=10, description="音色前缀")
    voice_prompt: str = Field(..., min_length=1, max_length=500, description="声音设计提示词")
    preview_text: str = Field(..., min_length=1, max_length=200, description="试听文本")
    language: Optional[str] = Field(default="zh", description="zh / en")
    sample_rate: int = Field(default=24000, description="试听音频采样率")
    response_format: str = Field(default="wav", description="试听音频格式：pcm/wav/mp3")
    enrollment_config_name: str = Field(default=tts_service.DEFAULT_ENROLLMENT_CONFIG_NAME)


class VoiceGenerateRequest(BaseModel):
    draft_id: Optional[int] = None
    voice_asset_id: Optional[int] = None
    voice_id: Optional[str] = Field(default=None, description="直接传第三方 voice_id，和 voice_asset_id 二选一")
    text: str = Field(..., min_length=1, description="待合成文本")
    style: Optional[str] = Field(default=None, description="风格描述，作为 instruct/instruction 透传")
    speed: Optional[float] = Field(default=1.0, ge=0.5, le=2.0)
    volume: Optional[float] = Field(default=1.0, ge=0.1, le=2.0)
    pitch: Optional[float] = Field(default=1.0, ge=0.5, le=2.0)
    language: Optional[str] = Field(default="zh")
    audio_format: str = Field(default="mp3")
    sample_rate: Optional[int] = Field(default=None)
    tts_config_name: str = Field(default=tts_service.DEFAULT_TTS_CONFIG_NAME)


@router.get("/voices")
async def list_voices(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    keyword: Optional[str] = Query(default=None),
    source_type: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default="enabled"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    data = await tts_service.list_voice_assets(
        keyword=keyword,
        source_type=source_type,
        status=status,
        page=page,
        page_size=page_size,
        user_id=current_user.user_id if current_user else None,
    )
    return {
        "code": 0,
        "message": "ok",
        "data": _to_absolute_urls(request, data),
    }


@router.post("/voices/clone")
async def clone_voice(
    request: Request,
    body: VoiceCloneRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        remote = await tts_service.create_voice_clone(
            enrollment_config_name=body.enrollment_config_name,
            target_model=body.target_model,
            prefix=body.prefix,
            audio_url=body.audio_url,
            language_hints=[body.language] if body.language else None,
            max_prompt_audio_length=body.max_prompt_audio_length,
            enable_preprocess=body.enable_preprocess,
        )
        data = await tts_service.create_local_voice_asset_from_clone(
            target_model=body.target_model,
            prefix=body.prefix,
            source_audio_url=body.audio_url,
            remote_response=remote,
            language=body.language,
            owner_user_id=current_user.user_id,
        )
        return {
            "code": 0,
            "message": "ok",
            "data": _to_absolute_urls(request, {**data, "raw": remote}),
        }
    except DashScopeTTSAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.payload or str(exc)) from exc
    except TTSServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/voices/design")
async def design_voice(
    request: Request,
    body: VoiceDesignRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        remote = await tts_service.create_voice_design(
            enrollment_config_name=body.enrollment_config_name,
            target_model=body.target_model,
            prefix=body.prefix,
            voice_prompt=body.voice_prompt,
            preview_text=body.preview_text,
            language_hints=[body.language] if body.language else None,
            sample_rate=body.sample_rate,
            response_format=body.response_format,
        )
        data = await tts_service.create_local_voice_asset_from_design(
            target_model=body.target_model,
            prefix=body.prefix,
            voice_prompt=body.voice_prompt,
            preview_text=body.preview_text,
            response_format=body.response_format,
            sample_rate=body.sample_rate,
            language=body.language,
            remote_response=remote,
            owner_user_id=current_user.user_id,
        )
        return {
            "code": 0,
            "message": "ok",
            "data": _to_absolute_urls(request, {**data, "raw": remote}),
        }
    except DashScopeTTSAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.payload or str(exc)) from exc
    except TTSServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/voices/{voice_id}")
async def get_voice_detail(
    request: Request,
    voice_id: str,
    enrollment_config_name: str = Query(default=tts_service.DEFAULT_ENROLLMENT_CONFIG_NAME),
):
    try:
        remote = await tts_service.query_remote_voice(
            enrollment_config_name=enrollment_config_name,
            voice_id=voice_id,
        )
        synced = await tts_service.sync_voice_asset_status(
            voice_id=voice_id,
            remote_output=remote.get("output") or {},
        )
        return {
            "code": 0,
            "message": "ok",
            "data": _to_absolute_urls(
                request,
                {
                    "voice_id": voice_id,
                    "voice_asset": synced,
                    "raw": remote,
                },
            ),
        }
    except DashScopeTTSAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.payload or str(exc)) from exc
    except TTSServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/voices/{voice_id}")
async def delete_voice(
    voice_id: str,
    enrollment_config_name: str = Query(default=tts_service.DEFAULT_ENROLLMENT_CONFIG_NAME),
):
    try:
        remote = await tts_service.delete_remote_voice(
            enrollment_config_name=enrollment_config_name,
            voice_id=voice_id,
        )
        await tts_service.soft_delete_voice_asset_by_voice_id(voice_id)
        return {
            "code": 0,
            "message": "ok",
            "data": {
                "voice_id": voice_id,
                "raw": remote,
            },
        }
    except DashScopeTTSAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.payload or str(exc)) from exc
    except TTSServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/generate")
async def generate_voice(
    request: Request,
    body: VoiceGenerateRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if not body.voice_asset_id and not (body.voice_id or "").strip():
        raise HTTPException(status_code=400, detail="voice_asset_id 和 voice_id 至少传一个")

    try:
        data = await tts_service.generate_audio(
            draft_id=body.draft_id,
            voice_asset_id=body.voice_asset_id,
            user_id=current_user.user_id if current_user else None,
            direct_voice_id=body.voice_id,
            text=body.text,
            style=body.style,
            speed=body.speed,
            volume=body.volume,
            pitch=body.pitch,
            language=body.language,
            audio_format=body.audio_format,
            sample_rate=body.sample_rate,
            tts_config_name=body.tts_config_name,
        )
        return {
            "code": 0,
            "message": "ok",
            "data": _to_absolute_urls(request, data),
        }
    except DashScopeTTSAPIError as exc:
        logger.warning("DashScope TTS API failed: {}", exc)
        raise HTTPException(status_code=exc.status_code, detail=exc.payload or str(exc)) from exc
    except TTSServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("generate_voice failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
