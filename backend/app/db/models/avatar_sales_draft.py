from __future__ import annotations

from sqlalchemy import JSON, BigInteger, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class AvatarSalesDraftModel(TimestampMixin, Base):
    __tablename__ = "avatar_draft_sales"

    draft_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
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
    product_keyword: Mapped[str | None] = mapped_column(String(255), nullable=True)
    selected_product_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    selected_product_profile: Mapped[dict] = mapped_column(JSON, default=dict)
    product_assets: Mapped[list] = mapped_column(JSON, default=list)
    selected_white_image_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    selected_wear_image_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    scene_image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    image_count: Mapped[int] = mapped_column(Integer, default=4)
    aspect_ratio: Mapped[str] = mapped_column(String(32), default="9:16")
    extra_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    fusion_task_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fusion_task_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fusion_images: Mapped[list] = mapped_column(JSON, default=list)
    selected_fusion_image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
