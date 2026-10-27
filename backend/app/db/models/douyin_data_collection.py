from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DouyinHotRankItem(Base):
    __tablename__ = "douyin_hot_rank_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(32))
    board_type: Mapped[str] = mapped_column(String(32))
    board_name: Mapped[str | None] = mapped_column(String(64))
    snapshot_no: Mapped[str] = mapped_column(String(64))
    snapshot_time: Mapped[datetime] = mapped_column(DateTime)
    rank: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255))
    word: Mapped[str | None] = mapped_column(String(255))
    hot_value: Mapped[int] = mapped_column(BigInteger)
    content_url: Mapped[str | None] = mapped_column(String(1024))
    cover_url: Mapped[str | None] = mapped_column(String(1024))
    aweme_id: Mapped[str | None] = mapped_column(String(64))
    event_time: Mapped[datetime | None] = mapped_column(DateTime)
    article_detail_count: Mapped[int] = mapped_column(Integer)
    discuss_video_count: Mapped[int] = mapped_column(Integer)
    video_count: Mapped[int] = mapped_column(Integer)
    room_count: Mapped[int] = mapped_column(Integer)
    label: Mapped[int | None] = mapped_column(Integer)
    label_url: Mapped[str | None] = mapped_column(String(1024))
    sentence_id: Mapped[str | None] = mapped_column(String(64))
    sentence_tag: Mapped[int | None] = mapped_column(Integer)
    raw_json: Mapped[dict | list | None] = mapped_column(JSON)
    crawled_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
