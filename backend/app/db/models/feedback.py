from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class FeedbackMetricModel(TimestampMixin, Base):
    __tablename__ = "feedback_metrics"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(64), index=True)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
