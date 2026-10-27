from __future__ import annotations

from pydantic import BaseModel, Field


class ParsePreviewRequest(BaseModel):
    task_id: str | None = None
    platform: str = "douyin"
    source_text: str


class ParseResult(BaseModel):
    platform: str
    summary: str
    selling_points: list[str] = Field(default_factory=list)
    detected_assets: list[str] = Field(default_factory=list)
