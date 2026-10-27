from __future__ import annotations

from sqlalchemy import JSON, BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class VideoEditTemplateModel(TimestampMixin, Base):
    __tablename__ = "user_video_edit_templates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(String(255), default="")
    template_type: Mapped[str] = mapped_column(String(32), default="clip", index=True)
    scene_code: Mapped[str] = mapped_column(String(64), default="digital_human_talk", index=True)
    render_config: Mapped[dict] = mapped_column(JSON, default=dict)
    editor_config: Mapped[dict] = mapped_column(JSON, default=dict)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    source_type: Mapped[str] = mapped_column(String(16), default="user", index=True)
    status: Mapped[str] = mapped_column(String(16), default="active", index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0, index=True)
