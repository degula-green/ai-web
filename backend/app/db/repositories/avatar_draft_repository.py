from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.avatar_draft import AvatarDraftModel


@dataclass(slots=True)
class AvatarDraftRecord:
    draft_id: str
    user_id: int
    scene_code: str
    title: str | None = None
    status: str = "draft"
    current_step_code: str | None = None
    progress: int | None = None
    is_deleted: int = 0
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_model(cls, model: AvatarDraftModel) -> "AvatarDraftRecord":
        return cls(
            draft_id=model.draft_id,
            user_id=model.user_id,
            scene_code=model.scene_code,
            title=model.title,
            status=model.status,
            current_step_code=model.current_step_code,
            progress=model.progress,
            is_deleted=model.is_deleted,
            created_at=model.created_at.isoformat() if model.created_at else "",
            updated_at=model.updated_at.isoformat() if model.updated_at else "",
        )


class AvatarDraftRepository:
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
        CREATE TABLE IF NOT EXISTS avatar_drafts (
            draft_id VARCHAR(64) PRIMARY KEY COMMENT '?? ID???????',
            user_id BIGINT UNSIGNED NOT NULL COMMENT '???? ID',
            scene_code VARCHAR(32) NOT NULL COMMENT '????????? talk?sales?product?model?clip',
            title VARCHAR(255) NULL COMMENT '????????????',
            status VARCHAR(32) NOT NULL DEFAULT 'draft' COMMENT '?????? draft?rewritten?completed?failed',
            current_step_code VARCHAR(64) NULL COMMENT '??????????????????',
            progress INT NULL COMMENT '????????? 0 ? 100',
            is_deleted TINYINT(1) NOT NULL DEFAULT 0 COMMENT '???????0 ?????1 ????',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '????',
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '????',
            KEY idx_avatar_drafts_user_scene_updated (user_id, scene_code, updated_at),
            KEY idx_avatar_drafts_user_updated (user_id, updated_at),
            KEY idx_avatar_drafts_scene_status (scene_code, status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='???????????????????????'
        """
        with self.session_scope() as session:
            session.execute(text(ddl))

    def get(self, draft_id: str, user_id: int) -> AvatarDraftRecord | None:
        with self.session_scope() as session:
            stmt = select(AvatarDraftModel).where(
                AvatarDraftModel.draft_id == draft_id,
                AvatarDraftModel.user_id == user_id,
                AvatarDraftModel.is_deleted == 0,
            )
            model = session.scalar(stmt)
            return AvatarDraftRecord.from_model(model) if model else None

    def list_by_user(
        self,
        user_id: int,
        *,
        scene_code: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[AvatarDraftRecord]:
        with self.session_scope() as session:
            stmt = (
                select(AvatarDraftModel)
                .where(
                    AvatarDraftModel.user_id == user_id,
                    AvatarDraftModel.is_deleted == 0,
                )
                .order_by(AvatarDraftModel.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )
            if scene_code:
                stmt = stmt.where(AvatarDraftModel.scene_code == scene_code)
            models = session.scalars(stmt).all()
            return [AvatarDraftRecord.from_model(model) for model in models]

    def upsert(self, record: AvatarDraftRecord) -> AvatarDraftRecord:
        with self.session_scope() as session:
            model = session.get(AvatarDraftModel, record.draft_id)
            if model is None:
                model = AvatarDraftModel(
                    draft_id=record.draft_id,
                    user_id=record.user_id,
                    scene_code=record.scene_code,
                    title=record.title,
                    status=record.status,
                    current_step_code=record.current_step_code,
                    progress=record.progress,
                    is_deleted=record.is_deleted,
                )
                session.add(model)
            else:
                model.user_id = record.user_id
                model.scene_code = record.scene_code
                model.title = record.title
                model.status = record.status
                model.current_step_code = record.current_step_code
                model.progress = record.progress
                model.is_deleted = record.is_deleted
            session.flush()
            return AvatarDraftRecord.from_model(model)

    def soft_delete(self, draft_id: str, user_id: int) -> bool:
        with self.session_scope() as session:
            stmt = select(AvatarDraftModel).where(
                AvatarDraftModel.draft_id == draft_id,
                AvatarDraftModel.user_id == user_id,
                AvatarDraftModel.is_deleted == 0,
            )
            model = session.scalar(stmt)
            if model is None:
                return False
            model.is_deleted = 1
            session.flush()
            return True
