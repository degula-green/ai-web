from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AvatarModelDraftCreateRequest(BaseModel):
    title: str | None = None
    product_keyword: str | None = None
    selected_product_id: str | None = None
    selected_product_profile: dict[str, Any] = Field(default_factory=dict)
    product_assets: list[dict[str, Any]] = Field(default_factory=list)
    selected_white_image_id: str | None = None
    selected_wear_image_id: str | None = None
    model_image_url: str | None = None
    scene_image_url: str | None = None
    image_count: int = Field(default=8, ge=1, le=20)
    aspect_ratio: str = "3:4"
    extra_requirements: str | None = None
    gallery_task_id: str | None = None
    gallery_task_status: str | None = None
    gallery_images: list[dict[str, Any]] = Field(default_factory=list)
    status: str = "draft"


class AvatarModelDraftUpdateRequest(BaseModel):
    title: str | None = None
    product_keyword: str | None = None
    selected_product_id: str | None = None
    selected_product_profile: dict[str, Any] | None = None
    product_assets: list[dict[str, Any]] | None = None
    selected_white_image_id: str | None = None
    selected_wear_image_id: str | None = None
    model_image_url: str | None = None
    scene_image_url: str | None = None
    image_count: int | None = Field(default=None, ge=1, le=20)
    aspect_ratio: str | None = None
    extra_requirements: str | None = None
    gallery_task_id: str | None = None
    gallery_task_status: str | None = None
    gallery_images: list[dict[str, Any]] | None = None
    status: str | None = None


class AvatarModelDraftRead(BaseModel):
    draft_id: str
    user_id: int
    title: str | None = None
    product_keyword: str | None = None
    selected_product_id: str | None = None
    selected_product_profile: dict[str, Any] = Field(default_factory=dict)
    product_assets: list[dict[str, Any]] = Field(default_factory=list)
    selected_white_image_id: str | None = None
    selected_wear_image_id: str | None = None
    model_image_url: str | None = None
    scene_image_url: str | None = None
    image_count: int
    aspect_ratio: str
    extra_requirements: str | None = None
    gallery_task_id: str | None = None
    gallery_task_status: str | None = None
    gallery_images: list[dict[str, Any]] = Field(default_factory=list)
    status: str
    created_at: str
    updated_at: str


class AvatarModelDraftListResponse(BaseModel):
    items: list[AvatarModelDraftRead] = Field(default_factory=list)
