from __future__ import annotations

from sqlalchemy import JSON, BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class CreationDraftModel(TimestampMixin, Base):
    __tablename__ = "avatar_draft_talk"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    platform: Mapped[str | None] = mapped_column(String(64), nullable=True)
    content_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_info: Mapped[dict] = mapped_column(JSON, default=dict)
    transcript: Mapped[dict] = mapped_column(JSON, default=dict)
    extracted_copy: Mapped[str | None] = mapped_column(Text, nullable=True)
    rewrite_instruction: Mapped[str | None] = mapped_column(Text, nullable=True)
    rewritten_copy: Mapped[str | None] = mapped_column(Text, nullable=True)
    voice_params: Mapped[dict] = mapped_column(JSON, default=dict)
    digital_human_params: Mapped[dict] = mapped_column(JSON, default=dict)
    clip_params: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
