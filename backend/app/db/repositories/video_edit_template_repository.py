from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import Select, asc, desc, or_, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.video_edit_template import VideoEditTemplateModel


@dataclass(slots=True)
class VideoEditTemplateRecord:
    id: int
    user_id: int | None
    name: str
    description: str = ""
    template_type: str = "clip"
    scene_code: str = "digital_human_talk"
    render_config: dict[str, Any] = field(default_factory=dict)
    editor_config: dict[str, Any] = field(default_factory=dict)
    thumbnail_url: str | None = None
    source_type: str = "user"
    status: str = "active"
    sort_order: int = 0
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_model(cls, model: VideoEditTemplateModel) -> "VideoEditTemplateRecord":
        return cls(
            id=int(model.id),
            user_id=model.user_id,
            name=model.name,
            description=model.description or "",
            template_type=model.template_type,
            scene_code=model.scene_code,
            render_config=model.render_config or {},
            editor_config=model.editor_config or {},
            thumbnail_url=model.thumbnail_url,
            source_type=model.source_type,
            status=model.status,
            sort_order=int(model.sort_order or 0),
            created_at=model.created_at.isoformat() if model.created_at else "",
            updated_at=model.updated_at.isoformat() if model.updated_at else "",
        )


class VideoEditTemplateRepository:
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
        CREATE TABLE IF NOT EXISTS user_video_edit_templates (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT NULL COMMENT '模板所属用户；官方模板为空',
            name VARCHAR(128) NOT NULL COMMENT '模板名称',
            description VARCHAR(255) NOT NULL DEFAULT '' COMMENT '模板说明',
            template_type VARCHAR(32) NOT NULL DEFAULT 'clip' COMMENT '模板类型',
            scene_code VARCHAR(64) NOT NULL DEFAULT 'digital_human_talk' COMMENT '适用业务场景',
            render_config JSON NOT NULL COMMENT 'FFmpeg/预览共用渲染配置',
            editor_config JSON NOT NULL COMMENT '前端编辑器状态',
            thumbnail_url VARCHAR(1024) NULL COMMENT '模板封面',
            source_type VARCHAR(16) NOT NULL DEFAULT 'user' COMMENT 'official/user',
            status VARCHAR(16) NOT NULL DEFAULT 'active',
            sort_order INT NOT NULL DEFAULT 0,
            is_deleted TINYINT NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            KEY idx_user_video_edit_templates_user_id (user_id),
            KEY idx_user_video_edit_templates_template_type (template_type),
            KEY idx_user_video_edit_templates_scene_code (scene_code),
            KEY idx_user_video_edit_templates_source_type (source_type),
            KEY idx_user_video_edit_templates_status (status),
            KEY idx_user_video_edit_templates_is_deleted (is_deleted),
            KEY idx_user_video_edit_templates_updated_at (updated_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='视频剪辑模板配置表'
        """
        with self.session_scope() as session:
            session.execute(text(ddl))

    def list_available(
        self,
        *,
        user_id: int,
        template_type: str | None = None,
        scene_code: str | None = None,
    ) -> list[VideoEditTemplateRecord]:
        with self.session_scope() as session:
            stmt: Select[tuple[VideoEditTemplateModel]] = select(VideoEditTemplateModel).where(
                VideoEditTemplateModel.is_deleted == 0,
                VideoEditTemplateModel.status == "active",
                or_(VideoEditTemplateModel.source_type == "official", VideoEditTemplateModel.user_id == user_id),
            )
            if template_type:
                stmt = stmt.where(VideoEditTemplateModel.template_type == template_type)
            if scene_code:
                stmt = stmt.where(VideoEditTemplateModel.scene_code == scene_code)

            stmt = stmt.order_by(
                asc(VideoEditTemplateModel.source_type),
                desc(VideoEditTemplateModel.sort_order),
                desc(VideoEditTemplateModel.updated_at),
                desc(VideoEditTemplateModel.id),
            )
            return [VideoEditTemplateRecord.from_model(item) for item in session.scalars(stmt).all()]

    def create_user_template(
        self,
        *,
        user_id: int,
        name: str,
        description: str,
        template_type: str,
        scene_code: str,
        render_config: dict[str, Any],
        editor_config: dict[str, Any],
        thumbnail_url: str | None,
    ) -> VideoEditTemplateRecord:
        with self.session_scope() as session:
            model = VideoEditTemplateModel(
                user_id=user_id,
                name=name,
                description=description,
                template_type=template_type,
                scene_code=scene_code,
                render_config=render_config,
                editor_config=editor_config,
                thumbnail_url=thumbnail_url,
                source_type="user",
                status="active",
            )
            session.add(model)
            session.flush()
            session.refresh(model)
            return VideoEditTemplateRecord.from_model(model)

    def update_user_template(
        self,
        *,
        user_id: int,
        template_id: int,
        values: dict[str, Any],
    ) -> VideoEditTemplateRecord | None:
        with self.session_scope() as session:
            model = session.scalar(
                select(VideoEditTemplateModel).where(
                    VideoEditTemplateModel.id == template_id,
                    VideoEditTemplateModel.user_id == user_id,
                    VideoEditTemplateModel.source_type == "user",
                    VideoEditTemplateModel.is_deleted == 0,
                )
            )
            if model is None:
                return None
            for key, value in values.items():
                setattr(model, key, value)
            session.flush()
            session.refresh(model)
            return VideoEditTemplateRecord.from_model(model)

    def soft_delete_user_template(self, *, user_id: int, template_id: int) -> bool:
        with self.session_scope() as session:
            model = session.scalar(
                select(VideoEditTemplateModel).where(
                    VideoEditTemplateModel.id == template_id,
                    VideoEditTemplateModel.user_id == user_id,
                    VideoEditTemplateModel.source_type == "user",
                    VideoEditTemplateModel.is_deleted == 0,
                )
            )
            if model is None:
                return False
            model.is_deleted = 1
            return True
