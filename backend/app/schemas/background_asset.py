from __future__ import annotations

from pydantic import BaseModel, Field


class BackgroundAssetCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    media_type: str = Field(pattern="^(image|video)$")
    asset_url: str = Field(min_length=1, max_length=1024)
    thumbnail_url: str | None = Field(default=None, max_length=1024)


class BackgroundAssetRead(BaseModel):
    id: int
    user_id: int | None = None
    name: str
    media_type: str
    asset_url: str
    thumbnail_url: str | None = None
    source_type: str
    status: str
    sort_order: int = 0
    created_at: str
    updated_at: str


class BackgroundAssetListResponse(BaseModel):
    items: list[BackgroundAssetRead] = Field(default_factory=list)
