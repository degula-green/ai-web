from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.creation_draft import CreationDraftRead


class ClipRenderRequest(BaseModel):
    """可选 body：由前端调用二创 transcribe-media-url 后传入，主后端不再配置 CONTENT_REMIX_*。"""

    segments: list[dict[str, Any]] | None = Field(
        default=None,
        description="ASR 分段 [{start, end, text}, ...]；有值则优先用于烧录字幕",
    )
    render_config: dict[str, Any] | None = Field(
        default=None,
        description="剪辑模板运行配置 JSON；前端预览和 FFmpeg 渲染共用同一份配置",
    )


class ClipRenderResponse(BaseModel):
    draft: CreationDraftRead
    srt_preview: str = Field(default="", description="生成的 SRT 文本，便于调试")
    playback_requires_auth: bool = Field(
        default=False,
        description="为 True 时前端需带 Bearer 请求 /clipped-video 拉流预览",
    )
