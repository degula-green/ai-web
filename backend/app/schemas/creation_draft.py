from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreationDraftCreateRequest(BaseModel):
    title: str | None = None
    source_url: str | None = None
    platform: str | None = None
    content_id: str | None = None
    content_info: dict[str, Any] = Field(default_factory=dict)
    transcript: dict[str, Any] = Field(default_factory=dict)
    extracted_copy: str | None = None
    rewrite_instruction: str | None = None
    rewritten_copy: str | None = None
    voice_params: dict[str, Any] = Field(default_factory=dict)
    digital_human_params: dict[str, Any] = Field(default_factory=dict)
    clip_params: dict[str, Any] = Field(default_factory=dict)
    status: str = "draft"


class CreationDraftUpdateRequest(BaseModel):
    title: str | None = None
    source_url: str | None = None
    platform: str | None = None
    content_id: str | None = None
    content_info: dict[str, Any] | None = None
    transcript: dict[str, Any] | None = None
    extracted_copy: str | None = None
    rewrite_instruction: str | None = None
    rewritten_copy: str | None = None
    voice_params: dict[str, Any] | None = None
    digital_human_params: dict[str, Any] | None = None
    clip_params: dict[str, Any] | None = None
    status: str | None = None


class CreationDraftRead(BaseModel):
    draft_id: str
    user_id: int
    title: str | None = None
    source_url: str | None = None
    platform: str | None = None
    content_id: str | None = None
    content_info: dict[str, Any] = Field(default_factory=dict)
    transcript: dict[str, Any] = Field(default_factory=dict)
    extracted_copy: str | None = None
    rewrite_instruction: str | None = None
    rewritten_copy: str | None = None
    voice_params: dict[str, Any] = Field(default_factory=dict)
    digital_human_params: dict[str, Any] = Field(default_factory=dict)
    clip_params: dict[str, Any] = Field(default_factory=dict)
    status: str
    created_at: str
    updated_at: str


class CreationDraftListResponse(BaseModel):
    items: list[CreationDraftRead] = Field(default_factory=list)


class DigitalHumanAssetUpdateRequest(BaseModel):
    media_type: str = Field(..., pattern="^(image|video)$")
    file_url: str = Field(..., min_length=1, max_length=2048)
    human_type: str | None = Field(default=None, pattern="^(image|video)$")
