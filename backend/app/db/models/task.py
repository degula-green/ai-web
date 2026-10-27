from sqlalchemy import JSON, String, BigInteger, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class TaskModel(TimestampMixin, Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    task_type: Mapped[str] = mapped_column(String(64), index=True)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    state: Mapped[str] = mapped_column(String(32), index=True)
    source_type: Mapped[str] = mapped_column(String(32))
    source_value: Mapped[str | None] = mapped_column(String(512), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
