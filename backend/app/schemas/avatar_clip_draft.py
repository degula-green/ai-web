from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AvatarClipDraftCreateRequest(BaseModel):
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
    selected_product_id: str | None = None
    selected_product_profile: dict[str, Any] = Field(default_factory=dict)
    product_assets: list[dict[str, Any]] = Field(default_factory=list)
    selected_selling_point_ids: list[str] = Field(default_factory=list)
    selected_clip_asset_ids: list[str] = Field(default_factory=list)
    selected_reference_asset_ids: list[str] = Field(default_factory=list)
    review_units: list[dict[str, Any]] = Field(default_factory=list)
    delete_segments: list[dict[str, Any]] = Field(default_factory=list)
    cut_summary: dict[str, Any] = Field(default_factory=dict)
    clipped_video_url: str | None = None
    clipped_audio_url: str | None = None
    avatar_source_mode: str = "image"
    avatar_image_url: str | None = None
    avatar_video_url: str | None = None
    generated_avatar_video_url: str | None = None
    generated_avatar_source_url: str | None = None
    avatar_task_id: str | None = None
    avatar_task_status: str | None = None
    overlay_position: str = "bottom-right"
    overlay_size_percent: int = Field(default=30, ge=5, le=80)
    overlay_shape: str = "square"
    overlay_border: bool = False
    overlay_shadow: bool = False
    overlay_plate: bool = False
    material_summary: str | None = None
    script_style: str | None = None
    duration_seconds: int = Field(default=180, ge=1, le=3600)
    render_plan: list[dict[str, Any]] = Field(default_factory=list)
    output_url: str | None = None
    current_step: str = "product"
    status: str = "draft"


class AvatarClipDraftUpdateRequest(BaseModel):
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
    selected_product_id: str | None = None
    selected_product_profile: dict[str, Any] | None = None
    product_assets: list[dict[str, Any]] | None = None
    selected_selling_point_ids: list[str] | None = None
    selected_clip_asset_ids: list[str] | None = None
    selected_reference_asset_ids: list[str] | None = None
    review_units: list[dict[str, Any]] | None = None
    delete_segments: list[dict[str, Any]] | None = None
    cut_summary: dict[str, Any] | None = None
    clipped_video_url: str | None = None
    clipped_audio_url: str | None = None
    avatar_source_mode: str | None = None
    avatar_image_url: str | None = None
    avatar_video_url: str | None = None
    generated_avatar_video_url: str | None = None
    generated_avatar_source_url: str | None = None
    avatar_task_id: str | None = None
    avatar_task_status: str | None = None
    overlay_position: str | None = None
    overlay_size_percent: int | None = Field(default=None, ge=5, le=80)
    overlay_shape: str | None = None
    overlay_border: bool | None = None
    overlay_shadow: bool | None = None
    overlay_plate: bool | None = None
    material_summary: str | None = None
    script_style: str | None = None
    duration_seconds: int | None = Field(default=None, ge=1, le=3600)
    render_plan: list[dict[str, Any]] | None = None
    output_url: str | None = None
    current_step: str | None = None
    status: str | None = None


class AvatarClipDraftRead(BaseModel):
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
    selected_product_id: str | None = None
    selected_product_profile: dict[str, Any] = Field(default_factory=dict)
    product_assets: list[dict[str, Any]] = Field(default_factory=list)
    selected_selling_point_ids: list[str] = Field(default_factory=list)
    selected_clip_asset_ids: list[str] = Field(default_factory=list)
    selected_reference_asset_ids: list[str] = Field(default_factory=list)
    review_units: list[dict[str, Any]] = Field(default_factory=list)
    delete_segments: list[dict[str, Any]] = Field(default_factory=list)
    cut_summary: dict[str, Any] = Field(default_factory=dict)
    clipped_video_url: str | None = None
    clipped_audio_url: str | None = None
    avatar_source_mode: str = "image"
    avatar_image_url: str | None = None
    avatar_video_url: str | None = None
    generated_avatar_video_url: str | None = None
    generated_avatar_source_url: str | None = None
    avatar_task_id: str | None = None
    avatar_task_status: str | None = None
    overlay_position: str = "bottom-right"
    overlay_size_percent: int = 30
    overlay_shape: str = "square"
    overlay_border: bool = False
    overlay_shadow: bool = False
    overlay_plate: bool = False
    material_summary: str | None = None
    script_style: str | None = None
    duration_seconds: int
    render_plan: list[dict[str, Any]] = Field(default_factory=list)
    output_url: str | None = None
    current_step: str
    status: str
    created_at: str
    updated_at: str


class AvatarClipDraftListResponse(BaseModel):
    items: list[AvatarClipDraftRead] = Field(default_factory=list)
