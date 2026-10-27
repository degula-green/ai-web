from __future__ import annotations

from sqlalchemy import JSON, BigInteger, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class AvatarModelDraftModel(TimestampMixin, Base):
    __tablename__ = "avatar_draft_model"

    draft_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_keyword: Mapped[str | None] = mapped_column(String(255), nullable=True)
    selected_product_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    selected_product_profile: Mapped[dict] = mapped_column(JSON, default=dict)
    product_assets: Mapped[dict] = mapped_column(JSON, default=list)
    selected_white_image_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    selected_wear_image_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    scene_image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    image_count: Mapped[int] = mapped_column(Integer, default=8)
    aspect_ratio: Mapped[str] = mapped_column(String(32), default="3:4")
    extra_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    gallery_task_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    gallery_task_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    gallery_images: Mapped[dict] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
