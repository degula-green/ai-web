from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import Select, delete, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.platform_account_content import PlatformAccountContent


@dataclass(slots=True)
class PlatformAccountContentRecord:
    owner_user_id: int
    account_id: int
    platform_code: str
    sec_user_id: str | None
    content_id: str
    content_type: str
    content_status: str
    dy_aweme_id: str | None = None
    xhs_note_id: str | None = None
    bili_video_id: str | None = None
    ks_video_id: str | None = None
    title: str | None = None
    cover_url: str | None = None
    content_url: str | None = None
    author_name: str | None = None
    aweme_type: str | None = None
    view_count: int = 0
    liked_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    published_at: datetime | None = None
    last_synced_at: datetime | None = None
    extra_data: dict[str, Any] | None = None


class PlatformAccountContentRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    @contextmanager
    def session_scope(self):
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def ensure_table(self) -> None:
        ddl = """
        CREATE TABLE IF NOT EXISTS platform_account_contents (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            owner_user_id BIGINT NOT NULL,
            account_id BIGINT NOT NULL,
            platform_code VARCHAR(32) NOT NULL,
            sec_user_id VARCHAR(255) NULL,
            content_id VARCHAR(128) NOT NULL,
            content_type VARCHAR(32) NOT NULL,
            content_status VARCHAR(32) NOT NULL,
            dy_aweme_id VARCHAR(64) NULL,
            xhs_note_id VARCHAR(64) NULL,
            bili_video_id VARCHAR(64) NULL,
            ks_video_id VARCHAR(64) NULL,
            title VARCHAR(255) NULL,
            cover_url VARCHAR(1024) NULL,
            content_url VARCHAR(2048) NULL,
            author_name VARCHAR(255) NULL,
            aweme_type VARCHAR(16) NULL,
            view_count INT NOT NULL DEFAULT 0,
            liked_count INT NOT NULL DEFAULT 0,
            comment_count INT NOT NULL DEFAULT 0,
            share_count INT NOT NULL DEFAULT 0,
            published_at DATETIME NULL,
            last_synced_at DATETIME NULL,
            extra_data JSON NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uk_pac_owner_account_platform_content (owner_user_id, account_id, platform_code, content_id),
            KEY idx_pac_owner_user_id (owner_user_id),
            KEY idx_pac_account_id (account_id),
            KEY idx_pac_platform_code (platform_code),
            KEY idx_pac_sec_user_id (sec_user_id),
            KEY idx_pac_content_status (content_status),
            KEY idx_pac_content_type (content_type),
            KEY idx_pac_published_at (published_at),
            KEY idx_pac_dy_aweme_id (dy_aweme_id),
            KEY idx_pac_xhs_note_id (xhs_note_id),
            KEY idx_pac_bili_video_id (bili_video_id),
            KEY idx_pac_ks_video_id (ks_video_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        with self.session_scope() as session:
            session.execute(text(ddl))
            try:
                session.execute(text("ALTER TABLE platform_account_contents ADD COLUMN view_count INT NOT NULL DEFAULT 0 AFTER aweme_type"))
            except Exception as exc:
                if "Duplicate column name" not in str(exc):
                    raise

    def replace_for_account(
        self,
        *,
        owner_user_id: int,
        account_id: int,
        platform_code: str,
        records: list[PlatformAccountContentRecord],
    ) -> None:
        with self.session_scope() as session:
            session.execute(
                delete(PlatformAccountContent).where(
                    PlatformAccountContent.owner_user_id == int(owner_user_id),
                    PlatformAccountContent.account_id == int(account_id),
                    PlatformAccountContent.platform_code == str(platform_code),
                )
            )
            for record in records:
                session.add(
                    PlatformAccountContent(
                        owner_user_id=record.owner_user_id,
                        account_id=record.account_id,
                        platform_code=record.platform_code,
                        sec_user_id=record.sec_user_id,
                        content_id=record.content_id,
                        content_type=record.content_type,
                        content_status=record.content_status,
                        dy_aweme_id=record.dy_aweme_id,
                        xhs_note_id=record.xhs_note_id,
                        bili_video_id=record.bili_video_id,
                        ks_video_id=record.ks_video_id,
                        title=record.title,
                        cover_url=record.cover_url,
                        content_url=record.content_url,
                        author_name=record.author_name,
                        aweme_type=record.aweme_type,
                        view_count=record.view_count,
                        liked_count=record.liked_count,
                        comment_count=record.comment_count,
                        share_count=record.share_count,
                        published_at=record.published_at,
                        last_synced_at=record.last_synced_at,
                        extra_data=record.extra_data,
                    )
                )

    def list_items(
        self,
        *,
        owner_user_id: int,
        platform_code: str | None = None,
        content_status: str | None = None,
        keyword: str | None = None,
    ) -> list[PlatformAccountContent]:
        with self.session_scope() as session:
            stmt: Select[tuple[PlatformAccountContent]] = (
                select(PlatformAccountContent)
                .where(PlatformAccountContent.owner_user_id == int(owner_user_id))
                .order_by(PlatformAccountContent.published_at.desc(), PlatformAccountContent.id.desc())
            )
            if platform_code:
                stmt = stmt.where(PlatformAccountContent.platform_code == platform_code)
            if content_status:
                stmt = stmt.where(PlatformAccountContent.content_status == content_status)
            if keyword:
                like_text = f"%{keyword.strip()}%"
                stmt = stmt.where(
                    (PlatformAccountContent.title.ilike(like_text))
                    | (PlatformAccountContent.content_id.ilike(like_text))
                )
            return list(session.scalars(stmt).all())
