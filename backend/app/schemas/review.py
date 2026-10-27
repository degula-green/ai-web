from __future__ import annotations

from pydantic import BaseModel, Field


class ReviewPreviewRequest(BaseModel):
    platform: str = "douyin"
    content: str


class ReviewResult(BaseModel):
    approved: bool
    score: float
    reasons: list[str] = Field(default_factory=list)


class ReviewClipSegment(BaseModel):
    start: float = Field(ge=0)
    end: float = Field(gt=0)


class ReviewClipVideoRequest(BaseModel):
    media_url: str = Field(min_length=1)
    delete_segments: list[ReviewClipSegment] = Field(default_factory=list)


class ReviewClipVideoResponse(BaseModel):
    clip_id: str
    playback_path: str
    playback_requires_auth: bool = True
    audio_playback_path: str | None = None
    audio_playback_requires_auth: bool = True
    original_duration: float = Field(ge=0)
    new_duration: float = Field(ge=0)
    deleted_duration: float = Field(ge=0)
    saved_percent: float = Field(ge=0)


class ReviewClipUploadResponse(ReviewClipVideoResponse):
    pass
