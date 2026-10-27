from __future__ import annotations

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class WorkflowDefModel(TimestampMixin, Base):
    __tablename__ = "workflow_defs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))


class WorkflowVersionModel(TimestampMixin, Base):
    __tablename__ = "workflow_versions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workflow_def_id: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[int] = mapped_column(Integer)
    definition: Mapped[dict] = mapped_column(JSON, default=dict)
