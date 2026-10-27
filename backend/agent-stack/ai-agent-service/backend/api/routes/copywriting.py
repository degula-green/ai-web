# -*- coding: utf-8 -*-
"""
轻量文案接口

- POST /api/v1/copywriting/extract
- POST /api/v1/copywriting/rewrite
- POST /api/v1/copywriting/transcribe-media-url  （成片/口播 ASR，与 01 相同鉴权方式）
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.dependencies import get_current_user_optional
from services.copywriting_service import copywriting_service
from services.main_auth_adapter import User
from utils.logger import logger

router = APIRouter()


class ExtractCopyRequest(BaseModel):
    url: str = Field(..., description="社媒内容链接")
    include_transcript_srt: bool = Field(
        default=False,
        description="为 True 且 ASR 有 segments 时，额外返回 transcript_srt（原片口播时间轴，可直接烧录/编辑）",
    )


class ExtractCopyResponse(BaseModel):
    url: str
    parsed_link: Dict[str, Any]
    content_info: Dict[str, Any]
    transcript: Optional[Dict[str, Any]] = None
    transcript_srt: Optional[str] = Field(
        default=None,
        description="由 transcript.segments 生成的标准 SRT（仅 include_transcript_srt 且转录成功时有值）",
    )
    extracted_copy: str
    llm_config_name: Optional[str] = None
    model_name: Optional[str] = None


class RewriteCopyRequest(BaseModel):
    text: str = Field(..., description="待改写文案")
    instruction: Optional[str] = Field(None, description="附加改写要求")


class RewriteCopyResponse(BaseModel):
    source_text: str
    rewritten_text: str
    instruction: Optional[str] = None
    llm_config_name: Optional[str] = None
    model_name: Optional[str] = None


class TranscribeMediaUrlRequest(BaseModel):
    media_url: str = Field(..., description="公网 http(s) 音视频直链，供 ASR（与 extract 转录链路一致）")


class TranscribeMediaUrlResponse(BaseModel):
    text: str
    segments: List[Dict[str, Any]]


@router.post("/transcribe-media-url", response_model=TranscribeMediaUrlResponse)
async def transcribe_media_url(
    body: TranscribeMediaUrlRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    剪辑路径乙：由前端携带与 extract 相同的 Bearer（若有）调用；不依赖主后端额外环境变量。
    """
    _ = current_user
    url = body.media_url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="media_url 须为 http(s)")
    from agent.tools.video_processor_tool import _process_video_internal

    try:
        logger.info("copywriting transcribe-media-url len={}", len(url))
        result = await _process_video_internal(url, step_callback=None, persist_video=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转写失败: {e}") from e
    segments_out: List[Dict[str, Any]] = []
    for seg in result.segments:
        if not isinstance(seg, dict):
            continue
        try:
            segments_out.append(
                {
                    "start": float(seg["start"]),
                    "end": float(seg["end"]),
                    "text": str(seg.get("text") or ""),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue
    return TranscribeMediaUrlResponse(text=result.text or "", segments=segments_out)


@router.post("/extract", response_model=ExtractCopyResponse)
async def extract_copy(
    request: ExtractCopyRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    try:
        result = await copywriting_service.extract_from_url(
            request.url,
            user_id=current_user.user_id if current_user else None,
            include_transcript_srt=request.include_transcript_srt,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文案提取失败: {e}") from e
    return ExtractCopyResponse(**result)


@router.post("/rewrite", response_model=RewriteCopyResponse)
async def rewrite_copy(request: RewriteCopyRequest):
    try:
        result = await copywriting_service.rewrite_text(
            request.text,
            instruction=request.instruction,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文案改写失败: {e}") from e
    return RewriteCopyResponse(**result)
