from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PlatformAccountContent(Base):
    __tablename__ = "platform_account_contents"
    __table_args__ = (
        UniqueConstraint(
            "owner_user_id",
            "account_id",
            "platform_code",
            "content_id",
            name="uk_pac_owner_account_platform_content",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    owner_user_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="Owner user id")
    account_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="platform_accounts.id")
    platform_code: Mapped[str] = mapped_column(String(32), index=True, comment="Platform code")
    sec_user_id: Mapped[str | None] = mapped_column(String(255), index=True, comment="Creator sec_user_id")
    content_id: Mapped[str] = mapped_column(String(128), index=True, comment="Generic platform content id")
    content_type: Mapped[str] = mapped_column(String(32), index=True, comment="video/image/unpublished")
    content_status: Mapped[str] = mapped_column(String(32), index=True, comment="published/pending")
    dy_aweme_id: Mapped[str | None] = mapped_column(String(64), index=True, comment="Douyin aweme id")
    xhs_note_id: Mapped[str | None] = mapped_column(String(64), index=True, comment="Xiaohongshu note id")
    bili_video_id: Mapped[str | None] = mapped_column(String(64), index=True, comment="Bilibili video id")
    ks_video_id: Mapped[str | None] = mapped_column(String(64), index=True, comment="Kuaishou video id")
    title: Mapped[str | None] = mapped_column(String(255), comment="Content title")
    cover_url: Mapped[str | None] = mapped_column(String(1024), comment="Cover URL")
    content_url: Mapped[str | None] = mapped_column(String(2048), comment="Content URL")
    author_name: Mapped[str | None] = mapped_column(String(255), comment="Author name")
    aweme_type: Mapped[str | None] = mapped_column(String(16), comment="Platform native content type")
    view_count: Mapped[int] = mapped_column(Integer, default=0, comment="View count")
    liked_count: Mapped[int] = mapped_column(Integer, default=0, comment="Like count")
    comment_count: Mapped[int] = mapped_column(Integer, default=0, comment="Comment count")
    share_count: Mapped[int] = mapped_column(Integer, default=0, comment="Share count")
    published_at: Mapped[datetime | None] = mapped_column(DateTime, index=True, comment="Platform publish time")
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, comment="Last sync time")
    extra_data: Mapped[dict | None] = mapped_column(JSON, comment="Extended metadata")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
