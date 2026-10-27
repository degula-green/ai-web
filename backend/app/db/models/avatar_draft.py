from __future__ import annotations

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class AvatarDraftModel(TimestampMixin, Base):
    __tablename__ = "avatar_drafts"

    draft_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    scene_code: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    current_step_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    progress: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0, index=True)
