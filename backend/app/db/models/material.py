from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class MaterialModel(TimestampMixin, Base):
    __tablename__ = "materials"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    material_type: Mapped[str] = mapped_column(String(32))
    source_value: Mapped[str] = mapped_column(String(1024))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
