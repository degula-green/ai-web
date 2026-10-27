from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class PublishPlanItemModel(TimestampMixin, Base):
    __tablename__ = "publish_plan_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    request_group_id: Mapped[str] = mapped_column(String(64), index=True)
    owner_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    draft_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    task_ref: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    platform_type: Mapped[int] = mapped_column(Integer, index=True)
    platform_code: Mapped[str] = mapped_column(String(32), index=True)
    platform_name: Mapped[str] = mapped_column(String(64))
    account_id: Mapped[int] = mapped_column(BigInteger, index=True)
    account_name: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))
    video_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    topics: Mapped[list] = mapped_column(JSON, default=list)
    publish_mode: Mapped[str] = mapped_column(String(32))
    publish_time_type: Mapped[str] = mapped_column(String(32), index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    status_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    downstream_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    downstream_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    downstream_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    extra_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
