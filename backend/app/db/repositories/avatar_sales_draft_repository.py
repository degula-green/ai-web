from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.avatar_sales_draft import AvatarSalesDraftModel


@dataclass(slots=True)
class AvatarSalesDraftRecord:
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
    product_keyword: str | None = None
    selected_product_id: str | None = None
    selected_product_profile: dict[str, Any] = field(default_factory=dict)
    product_assets: list[dict[str, Any]] = field(default_factory=list)
    selected_white_image_id: str | None = None
    selected_wear_image_id: str | None = None
    scene_image_url: str | None = None
    image_count: int = 4
    aspect_ratio: str = "9:16"
    extra_requirements: str | None = None
    fusion_task_id: str | None = None
    fusion_task_status: str | None = None
    fusion_images: list[dict[str, Any]] = field(default_factory=list)
    selected_fusion_image_url: str | None = None
    status: str = "draft"
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_model(cls, model: AvatarSalesDraftModel) -> "AvatarSalesDraftRecord":
        return cls(
            draft_id=model.draft_id,
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
            product_keyword=model.product_keyword,
            selected_product_id=model.selected_product_id,
            selected_product_profile=model.selected_product_profile or {},
            product_assets=model.product_assets or [],
            selected_white_image_id=model.selected_white_image_id,
            selected_wear_image_id=model.selected_wear_image_id,
            scene_image_url=model.scene_image_url,
            image_count=model.image_count,
            aspect_ratio=model.aspect_ratio,
            extra_requirements=model.extra_requirements,
            fusion_task_id=model.fusion_task_id,
            fusion_task_status=model.fusion_task_status,
            fusion_images=model.fusion_images or [],
            selected_fusion_image_url=model.selected_fusion_image_url,
            status=model.status,
            created_at=model.created_at.isoformat() if model.created_at else "",
            updated_at=model.updated_at.isoformat() if model.updated_at else "",
        )


class AvatarSalesDraftRepository:
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
        CREATE TABLE IF NOT EXISTS avatar_draft_sales (
            draft_id VARCHAR(64) PRIMARY KEY COMMENT '??????? ID',
            user_id BIGINT UNSIGNED NOT NULL COMMENT '???? ID',
            title VARCHAR(255) NULL COMMENT '????',
            source_url VARCHAR(2048) NULL COMMENT '????',
            platform VARCHAR(64) NULL COMMENT '????',
            content_id VARCHAR(128) NULL COMMENT '???? ID',
            content_info JSON NOT NULL COMMENT '????',
            transcript JSON NOT NULL COMMENT '????',
            extracted_copy TEXT NULL COMMENT '????',
            rewrite_instruction TEXT NULL COMMENT '????',
            rewritten_copy TEXT NULL COMMENT '????',
            voice_params JSON NOT NULL COMMENT '????',
            digital_human_params JSON NOT NULL COMMENT '?????',
            clip_params JSON NOT NULL COMMENT '????',
            product_keyword VARCHAR(255) NULL COMMENT '???????',
            selected_product_id VARCHAR(64) NULL COMMENT '???? ID',
            selected_product_profile JSON NOT NULL COMMENT '????????',
            product_assets JSON NOT NULL COMMENT '????????',
            selected_white_image_id VARCHAR(64) NULL COMMENT '??????? ID',
            selected_wear_image_id VARCHAR(64) NULL COMMENT '??????? ID',
            scene_image_url VARCHAR(2048) NULL COMMENT '?????',
            image_count INT NOT NULL DEFAULT 4 COMMENT '???????',
            aspect_ratio VARCHAR(32) NOT NULL DEFAULT '9:16' COMMENT '????',
            extra_requirements TEXT NULL COMMENT '????',
            fusion_task_id VARCHAR(64) NULL COMMENT '???? ID',
            fusion_task_status VARCHAR(32) NULL COMMENT '??????',
            fusion_images JSON NOT NULL COMMENT '????????',
            selected_fusion_image_url VARCHAR(2048) NULL COMMENT '??????????',
            status VARCHAR(32) NOT NULL DEFAULT 'draft' COMMENT '????',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '????',
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '????',
            KEY idx_avatar_draft_sales_user_updated (user_id, updated_at),
            KEY idx_avatar_draft_sales_user_status (user_id, status),
            KEY idx_avatar_draft_sales_product (selected_product_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='????????'
        """
        with self.session_scope() as session:
            session.execute(text(ddl))

    def create(self, record: AvatarSalesDraftRecord) -> AvatarSalesDraftRecord:
        with self.session_scope() as session:
            model = AvatarSalesDraftModel(
                draft_id=record.draft_id,
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
                product_keyword=record.product_keyword,
                selected_product_id=record.selected_product_id,
                selected_product_profile=record.selected_product_profile,
                product_assets=record.product_assets,
                selected_white_image_id=record.selected_white_image_id,
                selected_wear_image_id=record.selected_wear_image_id,
                scene_image_url=record.scene_image_url,
                image_count=record.image_count,
                aspect_ratio=record.aspect_ratio,
                extra_requirements=record.extra_requirements,
                fusion_task_id=record.fusion_task_id,
                fusion_task_status=record.fusion_task_status,
                fusion_images=record.fusion_images,
                selected_fusion_image_url=record.selected_fusion_image_url,
                status=record.status,
            )
            session.add(model)
            session.flush()
            return AvatarSalesDraftRecord.from_model(model)

    def get(self, draft_id: str, user_id: int) -> AvatarSalesDraftRecord | None:
        with self.session_scope() as session:
            stmt = select(AvatarSalesDraftModel).where(
                AvatarSalesDraftModel.draft_id == draft_id,
                AvatarSalesDraftModel.user_id == user_id,
            )
            model = session.scalar(stmt)
            return AvatarSalesDraftRecord.from_model(model) if model else None

    def list_by_user(self, user_id: int, *, limit: int = 20, offset: int = 0) -> list[AvatarSalesDraftRecord]:
        with self.session_scope() as session:
            stmt = (
                select(AvatarSalesDraftModel)
                .where(AvatarSalesDraftModel.user_id == user_id)
                .order_by(AvatarSalesDraftModel.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )
            models = session.scalars(stmt).all()
            return [AvatarSalesDraftRecord.from_model(model) for model in models]

    def update(self, record: AvatarSalesDraftRecord) -> AvatarSalesDraftRecord:
        with self.session_scope() as session:
            model = session.get(AvatarSalesDraftModel, record.draft_id)
            if model is None or model.user_id != record.user_id:
                raise ValueError(f"Avatar sales draft {record.draft_id} not found")
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
            model.product_keyword = record.product_keyword
            model.selected_product_id = record.selected_product_id
            model.selected_product_profile = record.selected_product_profile
            model.product_assets = record.product_assets
            model.selected_white_image_id = record.selected_white_image_id
            model.selected_wear_image_id = record.selected_wear_image_id
            model.scene_image_url = record.scene_image_url
            model.image_count = record.image_count
            model.aspect_ratio = record.aspect_ratio
            model.extra_requirements = record.extra_requirements
            model.fusion_task_id = record.fusion_task_id
            model.fusion_task_status = record.fusion_task_status
            model.fusion_images = record.fusion_images
            model.selected_fusion_image_url = record.selected_fusion_image_url
            model.status = record.status
            session.flush()
            return AvatarSalesDraftRecord.from_model(model)

    def delete(self, draft_id: str, user_id: int) -> bool:
        with self.session_scope() as session:
            stmt = select(AvatarSalesDraftModel).where(
                AvatarSalesDraftModel.draft_id == draft_id,
                AvatarSalesDraftModel.user_id == user_id,
            )
            model = session.scalar(stmt)
            if model is None:
                return False
            session.delete(model)
            session.flush()
            return True
