from __future__ import annotations

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class BackgroundAssetModel(TimestampMixin, Base):
    __tablename__ = "background_assets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    media_type: Mapped[str] = mapped_column(String(16), index=True)
    asset_url: Mapped[str] = mapped_column(String(1024))
    thumbnail_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    source_type: Mapped[str] = mapped_column(String(16), default="user", index=True)
    status: Mapped[str] = mapped_column(String(16), default="active", index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0, index=True)
