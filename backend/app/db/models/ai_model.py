from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AIModelProviderConfig(Base):
    __tablename__ = "ai_model_provider_configs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    provider_code: Mapped[str] = mapped_column(String(32), index=True)
    provider_name: Mapped[str] = mapped_column(String(64))
    base_url: Mapped[str] = mapped_column(String(255))
    api_key: Mapped[str] = mapped_column(String(255))
    default_model: Mapped[str] = mapped_column(String(128))
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=60)
    extra_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_test_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_test_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_test_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(BigInteger, default=0)
    updated_by: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class AITokenUsageLog(Base):
    __tablename__ = "ai_token_usage_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    task_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    scene: Mapped[str] = mapped_column(String(64), index=True)
    provider_code: Mapped[str] = mapped_column(String(32))
    model_name: Mapped[str] = mapped_column(String(128))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cached_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float] = mapped_column(Numeric(18, 6), default=0)
    currency: Mapped[str] = mapped_column(String(16), default="CNY")
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
