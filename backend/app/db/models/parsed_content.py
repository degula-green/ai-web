from __future__ import annotations

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ParsedContentModel(TimestampMixin, Base):
    __tablename__ = "parsed_contents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(64), index=True)
    summary: Mapped[str] = mapped_column(Text)
    structured_payload: Mapped[dict] = mapped_column(JSON, default=dict)
