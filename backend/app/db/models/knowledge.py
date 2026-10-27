from __future__ import annotations

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class KnowledgeItemModel(TimestampMixin, Base):
    __tablename__ = "knowledge_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    source: Mapped[str] = mapped_column(String(255))
    content_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
