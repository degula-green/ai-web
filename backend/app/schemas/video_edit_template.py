from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class VideoEditTemplateCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default="", max_length=255)
    template_type: str = Field(default="clip", max_length=32)
    scene_code: str = Field(default="digital_human_talk", max_length=64)
    render_config: dict[str, Any] = Field(default_factory=dict)
    editor_config: dict[str, Any] = Field(default_factory=dict)
    thumbnail_url: str | None = Field(default=None, max_length=1024)


class VideoEditTemplateUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=255)
    template_type: str | None = Field(default=None, max_length=32)
    scene_code: str | None = Field(default=None, max_length=64)
    render_config: dict[str, Any] | None = None
    editor_config: dict[str, Any] | None = None
    thumbnail_url: str | None = Field(default=None, max_length=1024)
    status: str | None = Field(default=None, pattern="^(active|disabled)$")


class VideoEditTemplateRead(BaseModel):
    id: int
    user_id: int | None = None
    name: str
    description: str = ""
    template_type: str
    scene_code: str
    render_config: dict[str, Any] = Field(default_factory=dict)
    editor_config: dict[str, Any] = Field(default_factory=dict)
    thumbnail_url: str | None = None
    source_type: str
    status: str
    sort_order: int = 0
    created_at: str
    updated_at: str


class VideoEditTemplateListResponse(BaseModel):
    items: list[VideoEditTemplateRead] = Field(default_factory=list)
