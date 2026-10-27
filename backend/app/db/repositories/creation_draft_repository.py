from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.creation_draft import CreationDraftModel


@dataclass(slots=True)
class CreationDraftRecord:
    draft_id: str
    user_id: int
    title: str | None = None
    source_url: str | None = None
    platform: str | None = None
    content_id: str | None = None
    content_info: dict[str, Any] = field(default_factory=dict)
    transcript: dict[str, Any] = field(default_factory=dict)
    extracted_copy: str | None = None
    rewrite_instruction: str | None = None
    rewritten_copy: str | None = None
    voice_params: dict[str, Any] = field(default_factory=dict)
    digital_human_params: dict[str, Any] = field(default_factory=dict)
    clip_params: dict[str, Any] = field(default_factory=dict)
    status: str = "draft"
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_model(cls, model: CreationDraftModel) -> CreationDraftRecord:
        return cls(
            draft_id=model.id,
            user_id=model.user_id,
            title=model.title,
            source_url=model.source_url,
            platform=model.platform,
            content_id=model.content_id,
            content_info=model.content_info or {},
            transcript=model.transcript or {},
            extracted_copy=model.extracted_copy,
            rewrite_instruction=model.rewrite_instruction,
            rewritten_copy=model.rewritten_copy,
            voice_params=model.voice_params or {},
            digital_human_params=model.digital_human_params or {},
            clip_params=model.clip_params or {},
            status=model.status,
            created_at=model.created_at.isoformat() if model.created_at else "",
            updated_at=model.updated_at.isoformat() if model.updated_at else "",
        )


class CreationDraftRepository:
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
        CREATE TABLE IF NOT EXISTS avatar_draft_talk (
            id VARCHAR(64) PRIMARY KEY COMMENT '草稿 ID',
            user_id BIGINT NOT NULL COMMENT '用户 ID',
            title VARCHAR(255) NULL COMMENT '草稿标题',
            source_url VARCHAR(1024) NULL COMMENT '来源链接',
            platform VARCHAR(64) NULL COMMENT '来源平台',
            content_id VARCHAR(255) NULL COMMENT '来源内容 ID',
            content_info JSON NOT NULL COMMENT '内容信息',
            transcript JSON NOT NULL COMMENT '转录结果',
            extracted_copy TEXT NULL COMMENT '提取文案',
            rewrite_instruction TEXT NULL COMMENT '改写指令',
            rewritten_copy TEXT NULL COMMENT '改写文案',
            voice_params JSON NOT NULL COMMENT '配音参数',
            digital_human_params JSON NOT NULL COMMENT '数字人参数',
            clip_params JSON NOT NULL COMMENT '剪辑参数',
            status VARCHAR(32) NOT NULL DEFAULT 'draft' COMMENT '草稿状态',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            KEY idx_avatar_draft_talk_user_id (user_id),
            KEY idx_avatar_draft_talk_status (status),
            KEY idx_avatar_draft_talk_updated_at (updated_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='口播数字人草稿表'
        """
        migrate_sql = """
        INSERT INTO avatar_draft_talk (
            id, user_id, title, source_url, platform, content_id,
            content_info, transcript, extracted_copy, rewrite_instruction,
            rewritten_copy, voice_params, digital_human_params, clip_params,
            status, created_at, updated_at
        )
        SELECT
            old.id, old.user_id, old.title, old.source_url, old.platform, old.content_id,
            old.content_info, old.transcript, old.extracted_copy, old.rewrite_instruction,
            old.rewritten_copy, old.voice_params, old.digital_human_params, old.clip_params,
            old.status, old.created_at, old.updated_at
        FROM creation_drafts AS old
        WHERE EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
              AND table_name = 'creation_drafts'
        )
          AND NOT EXISTS (
            SELECT 1
            FROM avatar_draft_talk AS new_table
            WHERE new_table.id = old.id
        )
        """
        with self.session_scope() as session:
            session.execute(text(ddl))
            if self._table_exists(session, "creation_drafts"):
                session.execute(text(migrate_sql))

    @staticmethod
    def _table_exists(session: Session, table_name: str) -> bool:
        stmt = text(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = DATABASE() AND table_name = :table_name
            LIMIT 1
            """
        )
        return session.execute(stmt, {"table_name": table_name}).first() is not None

    def create(self, record: CreationDraftRecord) -> CreationDraftRecord:
        with self.session_scope() as session:
            model = CreationDraftModel(
                id=record.draft_id,
                user_id=record.user_id,
                title=record.title,
                source_url=record.source_url,
                platform=record.platform,
                content_id=record.content_id,
                content_info=record.content_info,
                transcript=record.transcript,
                extracted_copy=record.extracted_copy,
                rewrite_instruction=record.rewrite_instruction,
                rewritten_copy=record.rewritten_copy,
                voice_params=record.voice_params,
                digital_human_params=record.digital_human_params,
                clip_params=record.clip_params,
                status=record.status,
            )
            session.add(model)
            session.flush()
            return CreationDraftRecord.from_model(model)

    def get(self, draft_id: str, user_id: int) -> CreationDraftRecord | None:
        with self.session_scope() as session:
            stmt = select(CreationDraftModel).where(
                CreationDraftModel.id == draft_id,
                CreationDraftModel.user_id == user_id,
            )
            model = session.scalar(stmt)
            return CreationDraftRecord.from_model(model) if model else None

    def list_by_user(self, user_id: int, *, limit: int = 20, offset: int = 0) -> list[CreationDraftRecord]:
        with self.session_scope() as session:
            stmt = (
                select(CreationDraftModel)
                .where(CreationDraftModel.user_id == user_id)
                .order_by(CreationDraftModel.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )
            models = session.scalars(stmt).all()
            return [CreationDraftRecord.from_model(model) for model in models]

    def list_all(self) -> list[CreationDraftRecord]:
        with self.session_scope() as session:
            stmt = select(CreationDraftModel).order_by(CreationDraftModel.updated_at.desc())
            models = session.scalars(stmt).all()
            return [CreationDraftRecord.from_model(model) for model in models]

    def update(self, record: CreationDraftRecord) -> CreationDraftRecord:
        with self.session_scope() as session:
            model = session.get(CreationDraftModel, record.draft_id)
            if model is None or model.user_id != record.user_id:
                raise ValueError(f"Creation draft {record.draft_id} not found")

            model.title = record.title
            model.source_url = record.source_url
            model.platform = record.platform
            model.content_id = record.content_id
            model.content_info = record.content_info
            model.transcript = record.transcript
            model.extracted_copy = record.extracted_copy
            model.rewrite_instruction = record.rewrite_instruction
            model.rewritten_copy = record.rewritten_copy
            model.voice_params = record.voice_params
            model.digital_human_params = record.digital_human_params
            model.clip_params = record.clip_params
            model.status = record.status
            session.flush()
            return CreationDraftRecord.from_model(model)

    def delete(self, draft_id: str, user_id: int) -> bool:
        with self.session_scope() as session:
            stmt = select(CreationDraftModel).where(
                CreationDraftModel.id == draft_id,
                CreationDraftModel.user_id == user_id,
            )
            model = session.scalar(stmt)
            if model is None:
                return False
            session.delete(model)
            session.flush()
            return True
