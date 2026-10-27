from __future__ import annotations

from pydantic import BaseModel, Field


class AvatarDraftRead(BaseModel):
    draft_id: str
    user_id: int
    scene_code: str
    title: str | None = None
    status: str
    current_step_code: str | None = None
    progress: int | None = None
    created_at: str
    updated_at: str


class AvatarDraftListResponse(BaseModel):
    items: list[AvatarDraftRead] = Field(default_factory=list)
