from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.avatar_model_draft import AvatarModelDraftModel


@dataclass(slots=True)
class AvatarModelDraftRecord:
    draft_id: str
    user_id: int
    title: str | None = None
    product_keyword: str | None = None
    selected_product_id: str | None = None
    selected_product_profile: dict[str, Any] = field(default_factory=dict)
    product_assets: list[dict[str, Any]] = field(default_factory=list)
    selected_white_image_id: str | None = None
    selected_wear_image_id: str | None = None
    model_image_url: str | None = None
    scene_image_url: str | None = None
    image_count: int = 8
    aspect_ratio: str = "3:4"
    extra_requirements: str | None = None
    gallery_task_id: str | None = None
    gallery_task_status: str | None = None
    gallery_images: list[dict[str, Any]] = field(default_factory=list)
    status: str = "draft"
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_model(cls, model: AvatarModelDraftModel) -> "AvatarModelDraftRecord":
        return cls(
            draft_id=model.draft_id,
            user_id=model.user_id,
            title=model.title,
            product_keyword=model.product_keyword,
            selected_product_id=model.selected_product_id,
            selected_product_profile=model.selected_product_profile or {},
            product_assets=model.product_assets or [],
            selected_white_image_id=model.selected_white_image_id,
            selected_wear_image_id=model.selected_wear_image_id,
            model_image_url=model.model_image_url,
            scene_image_url=model.scene_image_url,
            image_count=model.image_count,
            aspect_ratio=model.aspect_ratio,
            extra_requirements=model.extra_requirements,
            gallery_task_id=model.gallery_task_id,
            gallery_task_status=model.gallery_task_status,
            gallery_images=model.gallery_images or [],
            status=model.status,
            created_at=model.created_at.isoformat() if model.created_at else "",
            updated_at=model.updated_at.isoformat() if model.updated_at else "",
        )


class AvatarModelDraftRepository:
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
        CREATE TABLE IF NOT EXISTS avatar_draft_model (
            draft_id VARCHAR(64) PRIMARY KEY COMMENT '??????? ID??? avatar_drafts.draft_id',
            user_id BIGINT UNSIGNED NOT NULL COMMENT '???? ID',
            title VARCHAR(255) NULL COMMENT '????',
            product_keyword VARCHAR(255) NULL COMMENT '???????',
            selected_product_id VARCHAR(64) NULL COMMENT '?????? ID',
            selected_product_profile JSON NOT NULL COMMENT '?????????',
            product_assets JSON NOT NULL COMMENT '??????????',
            selected_white_image_id VARCHAR(64) NULL COMMENT '??????? ID',
            selected_wear_image_id VARCHAR(64) NULL COMMENT '??????? ID',
            model_image_url VARCHAR(2048) NULL COMMENT '?????',
            scene_image_url VARCHAR(2048) NULL COMMENT '???????',
            image_count INT NOT NULL DEFAULT 8 COMMENT '??????????',
            aspect_ratio VARCHAR(32) NOT NULL DEFAULT '3:4' COMMENT '?????',
            extra_requirements TEXT NULL COMMENT '????',
            gallery_task_id VARCHAR(64) NULL COMMENT '?????? ID',
            gallery_task_status VARCHAR(32) NULL COMMENT '????????',
            gallery_images JSON NOT NULL COMMENT '???????????',
            status VARCHAR(32) NOT NULL DEFAULT 'draft' COMMENT '?????????',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '????',
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '????',
            KEY idx_avatar_draft_model_user_updated (user_id, updated_at),
            KEY idx_avatar_draft_model_user_status (user_id, status),
            KEY idx_avatar_draft_model_product (selected_product_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='????????'
        """
        with self.session_scope() as session:
            session.execute(text(ddl))

    def create(self, record: AvatarModelDraftRecord) -> AvatarModelDraftRecord:
        with self.session_scope() as session:
            model = AvatarModelDraftModel(
                draft_id=record.draft_id,
                user_id=record.user_id,
                title=record.title,
                product_keyword=record.product_keyword,
                selected_product_id=record.selected_product_id,
                selected_product_profile=record.selected_product_profile,
                product_assets=record.product_assets,
                selected_white_image_id=record.selected_white_image_id,
                selected_wear_image_id=record.selected_wear_image_id,
                model_image_url=record.model_image_url,
                scene_image_url=record.scene_image_url,
                image_count=record.image_count,
                aspect_ratio=record.aspect_ratio,
                extra_requirements=record.extra_requirements,
                gallery_task_id=record.gallery_task_id,
                gallery_task_status=record.gallery_task_status,
                gallery_images=record.gallery_images,
                status=record.status,
            )
            session.add(model)
            session.flush()
            return AvatarModelDraftRecord.from_model(model)

    def get(self, draft_id: str, user_id: int) -> AvatarModelDraftRecord | None:
        with self.session_scope() as session:
            stmt = select(AvatarModelDraftModel).where(
                AvatarModelDraftModel.draft_id == draft_id,
                AvatarModelDraftModel.user_id == user_id,
            )
            model = session.scalar(stmt)
            return AvatarModelDraftRecord.from_model(model) if model else None

    def list_by_user(self, user_id: int, *, limit: int = 20, offset: int = 0) -> list[AvatarModelDraftRecord]:
        with self.session_scope() as session:
            stmt = (
                select(AvatarModelDraftModel)
                .where(AvatarModelDraftModel.user_id == user_id)
                .order_by(AvatarModelDraftModel.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )
            models = session.scalars(stmt).all()
            return [AvatarModelDraftRecord.from_model(model) for model in models]

    def update(self, record: AvatarModelDraftRecord) -> AvatarModelDraftRecord:
        with self.session_scope() as session:
            model = session.get(AvatarModelDraftModel, record.draft_id)
            if model is None or model.user_id != record.user_id:
                raise ValueError(f"Avatar model draft {record.draft_id} not found")
            model.title = record.title
            model.product_keyword = record.product_keyword
            model.selected_product_id = record.selected_product_id
            model.selected_product_profile = record.selected_product_profile
            model.product_assets = record.product_assets
            model.selected_white_image_id = record.selected_white_image_id
            model.selected_wear_image_id = record.selected_wear_image_id
            model.model_image_url = record.model_image_url
            model.scene_image_url = record.scene_image_url
            model.image_count = record.image_count
            model.aspect_ratio = record.aspect_ratio
            model.extra_requirements = record.extra_requirements
            model.gallery_task_id = record.gallery_task_id
            model.gallery_task_status = record.gallery_task_status
            model.gallery_images = record.gallery_images
            model.status = record.status
            session.flush()
            return AvatarModelDraftRecord.from_model(model)

    def delete(self, draft_id: str, user_id: int) -> bool:
        with self.session_scope() as session:
            stmt = select(AvatarModelDraftModel).where(
                AvatarModelDraftModel.draft_id == draft_id,
                AvatarModelDraftModel.user_id == user_id,
            )
            model = session.scalar(stmt)
            if model is None:
                return False
            session.delete(model)
            session.flush()
            return True
