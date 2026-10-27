from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AvatarSalesDraftCreateRequest(BaseModel):
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
    product_keyword: str | None = None
    selected_product_id: str | None = None
    selected_product_profile: dict[str, Any] = Field(default_factory=dict)
    product_assets: list[dict[str, Any]] = Field(default_factory=list)
    selected_white_image_id: str | None = None
    selected_wear_image_id: str | None = None
    scene_image_url: str | None = None
    image_count: int = Field(default=4, ge=1, le=20)
    aspect_ratio: str = "9:16"
    extra_requirements: str | None = None
    fusion_task_id: str | None = None
    fusion_task_status: str | None = None
    fusion_images: list[dict[str, Any]] = Field(default_factory=list)
    selected_fusion_image_url: str | None = None
    status: str = "draft"


class AvatarSalesDraftUpdateRequest(BaseModel):
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
    product_keyword: str | None = None
    selected_product_id: str | None = None
    selected_product_profile: dict[str, Any] | None = None
    product_assets: list[dict[str, Any]] | None = None
    selected_white_image_id: str | None = None
    selected_wear_image_id: str | None = None
    scene_image_url: str | None = None
    image_count: int | None = Field(default=None, ge=1, le=20)
    aspect_ratio: str | None = None
    extra_requirements: str | None = None
    fusion_task_id: str | None = None
    fusion_task_status: str | None = None
    fusion_images: list[dict[str, Any]] | None = None
    selected_fusion_image_url: str | None = None
    status: str | None = None


class AvatarSalesDraftRead(BaseModel):
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
    product_keyword: str | None = None
    selected_product_id: str | None = None
    selected_product_profile: dict[str, Any] = Field(default_factory=dict)
    product_assets: list[dict[str, Any]] = Field(default_factory=list)
    selected_white_image_id: str | None = None
    selected_wear_image_id: str | None = None
    scene_image_url: str | None = None
    image_count: int
    aspect_ratio: str
    extra_requirements: str | None = None
    fusion_task_id: str | None = None
    fusion_task_status: str | None = None
    fusion_images: list[dict[str, Any]] = Field(default_factory=list)
    selected_fusion_image_url: str | None = None
    status: str
    created_at: str
    updated_at: str


class AvatarSalesDraftListResponse(BaseModel):
    items: list[AvatarSalesDraftRead] = Field(default_factory=list)
