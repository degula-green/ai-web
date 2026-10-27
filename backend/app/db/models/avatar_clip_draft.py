from __future__ import annotations

from sqlalchemy import JSON, BigInteger, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class AvatarClipDraftModel(TimestampMixin, Base):
    __tablename__ = "avatar_draft_clip"

    draft_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    platform: Mapped[str | None] = mapped_column(String(64), nullable=True)
    content_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    content_info: Mapped[dict] = mapped_column(JSON, default=dict)
    transcript: Mapped[dict] = mapped_column(JSON, default=dict)
    extracted_copy: Mapped[str | None] = mapped_column(Text, nullable=True)
    rewrite_instruction: Mapped[str | None] = mapped_column(Text, nullable=True)
    rewritten_copy: Mapped[str | None] = mapped_column(Text, nullable=True)
    voice_params: Mapped[dict] = mapped_column(JSON, default=dict)
    digital_human_params: Mapped[dict] = mapped_column(JSON, default=dict)
    clip_params: Mapped[dict] = mapped_column(JSON, default=dict)
    selected_product_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    selected_product_profile: Mapped[dict] = mapped_column(JSON, default=dict)
    product_assets: Mapped[list] = mapped_column(JSON, default=list)
    selected_selling_point_ids: Mapped[list] = mapped_column(JSON, default=list)
    selected_clip_asset_ids: Mapped[list] = mapped_column(JSON, default=list)
    selected_reference_asset_ids: Mapped[list] = mapped_column(JSON, default=list)
    review_units: Mapped[list] = mapped_column(JSON, default=list)
    delete_segments: Mapped[list] = mapped_column(JSON, default=list)
    cut_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    clipped_video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    clipped_audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_source_mode: Mapped[str] = mapped_column(String(16), default="image")
    avatar_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_avatar_video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_avatar_source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_task_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    avatar_task_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    overlay_position: Mapped[str] = mapped_column(String(32), default="bottom-right")
    overlay_size_percent: Mapped[int] = mapped_column(Integer, default=30)
    overlay_shape: Mapped[str] = mapped_column(String(32), default="square")
    overlay_border: Mapped[int] = mapped_column(Integer, default=0)
    overlay_shadow: Mapped[int] = mapped_column(Integer, default=0)
    overlay_plate: Mapped[int] = mapped_column(Integer, default=0)
    material_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    script_style: Mapped[str | None] = mapped_column(String(64), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=180)
    render_plan: Mapped[list] = mapped_column(JSON, default=list)
    output_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_step: Mapped[str] = mapped_column(String(32), default="product")
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
