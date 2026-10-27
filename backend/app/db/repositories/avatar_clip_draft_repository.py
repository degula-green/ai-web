from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.avatar_clip_draft import AvatarClipDraftModel


@dataclass(slots=True)
class AvatarClipDraftRecord:
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
    selected_product_id: str | None = None
    selected_product_profile: dict[str, Any] = field(default_factory=dict)
    product_assets: list[dict[str, Any]] = field(default_factory=list)
    selected_selling_point_ids: list[str] = field(default_factory=list)
    selected_clip_asset_ids: list[str] = field(default_factory=list)
    selected_reference_asset_ids: list[str] = field(default_factory=list)
    review_units: list[dict[str, Any]] = field(default_factory=list)
    delete_segments: list[dict[str, Any]] = field(default_factory=list)
    cut_summary: dict[str, Any] = field(default_factory=dict)
    clipped_video_url: str | None = None
    clipped_audio_url: str | None = None
    avatar_source_mode: str = "image"
    avatar_image_url: str | None = None
    avatar_video_url: str | None = None
    generated_avatar_video_url: str | None = None
    generated_avatar_source_url: str | None = None
    avatar_task_id: str | None = None
    avatar_task_status: str | None = None
    overlay_position: str = "bottom-right"
    overlay_size_percent: int = 30
    overlay_shape: str = "square"
    overlay_border: bool = False
    overlay_shadow: bool = False
    overlay_plate: bool = False
    material_summary: str | None = None
    script_style: str | None = None
    duration_seconds: int = 180
    render_plan: list[dict[str, Any]] = field(default_factory=list)
    output_url: str | None = None
    current_step: str = "product"
    status: str = "draft"
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_model(cls, model: AvatarClipDraftModel) -> "AvatarClipDraftRecord":
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
            selected_product_id=model.selected_product_id,
            selected_product_profile=model.selected_product_profile or {},
            product_assets=model.product_assets or [],
            selected_selling_point_ids=model.selected_selling_point_ids or [],
            selected_clip_asset_ids=model.selected_clip_asset_ids or [],
            selected_reference_asset_ids=model.selected_reference_asset_ids or [],
            review_units=model.review_units or [],
            delete_segments=model.delete_segments or [],
            cut_summary=model.cut_summary or {},
            clipped_video_url=model.clipped_video_url,
            clipped_audio_url=model.clipped_audio_url,
            avatar_source_mode=model.avatar_source_mode or "image",
            avatar_image_url=model.avatar_image_url,
            avatar_video_url=model.avatar_video_url,
            generated_avatar_video_url=model.generated_avatar_video_url,
            generated_avatar_source_url=model.generated_avatar_source_url,
            avatar_task_id=model.avatar_task_id,
            avatar_task_status=model.avatar_task_status,
            overlay_position=model.overlay_position or "bottom-right",
            overlay_size_percent=model.overlay_size_percent or 30,
            overlay_shape=model.overlay_shape or "square",
            overlay_border=bool(model.overlay_border),
            overlay_shadow=bool(model.overlay_shadow),
            overlay_plate=bool(model.overlay_plate),
            material_summary=model.material_summary,
            script_style=model.script_style,
            duration_seconds=model.duration_seconds,
            render_plan=model.render_plan or [],
            output_url=model.output_url,
            current_step=model.current_step or "product",
            status=model.status,
            created_at=model.created_at.isoformat() if model.created_at else "",
            updated_at=model.updated_at.isoformat() if model.updated_at else "",
        )


class AvatarClipDraftRepository:
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
        CREATE TABLE IF NOT EXISTS avatar_draft_clip (
            draft_id VARCHAR(64) PRIMARY KEY COMMENT '草稿 ID',
            user_id BIGINT UNSIGNED NOT NULL COMMENT '用户 ID',
            title VARCHAR(255) NULL COMMENT '草稿标题',
            source_url TEXT NULL COMMENT '来源视频链接',
            platform VARCHAR(64) NULL COMMENT '来源平台',
            content_id VARCHAR(128) NULL COMMENT '来源内容 ID',
            content_info JSON NOT NULL COMMENT '通用内容信息',
            transcript JSON NOT NULL COMMENT '转录原始结果',
            extracted_copy TEXT NULL COMMENT '提取文案',
            rewrite_instruction TEXT NULL COMMENT '改写指令',
            rewritten_copy TEXT NULL COMMENT '改写文案',
            voice_params JSON NOT NULL COMMENT '配音参数',
            digital_human_params JSON NOT NULL COMMENT '数字人通用参数',
            clip_params JSON NOT NULL COMMENT '剪辑通用参数',
            selected_product_id VARCHAR(64) NULL COMMENT '第 01 步选中的产品 ID',
            selected_product_profile JSON NOT NULL COMMENT '第 01 步产品快照',
            product_assets JSON NOT NULL COMMENT '第 01 步产品素材快照',
            selected_selling_point_ids JSON NOT NULL COMMENT '第 01 步选中的卖点 ID 列表',
            selected_clip_asset_ids JSON NOT NULL COMMENT '第 01 步选中的剪辑视频素材 ID 列表',
            selected_reference_asset_ids JSON NOT NULL COMMENT '第 01 步选中的参考素材 ID 列表',
            review_units JSON NOT NULL COMMENT '第 02 步审核单元列表',
            delete_segments JSON NOT NULL COMMENT '第 02 步确认删除的时间区间',
            cut_summary JSON NOT NULL COMMENT '第 02 步剪辑结果摘要',
            clipped_video_url TEXT NULL COMMENT '第 02 步剪辑后视频地址',
            clipped_audio_url TEXT NULL COMMENT '第 02 步剪辑后音频地址',
            avatar_source_mode VARCHAR(16) NOT NULL DEFAULT 'image' COMMENT '第 03 步数字人素材类型：image/video',
            avatar_image_url TEXT NULL COMMENT '第 03 步数字人图片素材地址',
            avatar_video_url TEXT NULL COMMENT '第 03 步数字人视频素材地址',
            generated_avatar_video_url TEXT NULL COMMENT '第 03 步生成后的数字人视频地址',
            generated_avatar_source_url TEXT NULL COMMENT '第 03 步生成服务原始结果地址',
            avatar_task_id VARCHAR(128) NULL COMMENT '第 03 步数字人生成任务 ID',
            avatar_task_status VARCHAR(64) NULL COMMENT '第 03 步数字人生成任务状态',
            overlay_position VARCHAR(32) NOT NULL DEFAULT 'bottom-right' COMMENT '第 04 步数字人叠加位置',
            overlay_size_percent INT NOT NULL DEFAULT 30 COMMENT '第 04 步数字人叠加尺寸百分比',
            overlay_shape VARCHAR(32) NOT NULL DEFAULT 'square' COMMENT '第 04 步数字人叠加形状',
            overlay_border TINYINT(1) NOT NULL DEFAULT 0 COMMENT '第 04 步是否显示边框',
            overlay_shadow TINYINT(1) NOT NULL DEFAULT 0 COMMENT '第 04 步是否显示阴影',
            overlay_plate TINYINT(1) NOT NULL DEFAULT 0 COMMENT '第 04 步是否显示底板',
            material_summary TEXT NULL COMMENT '素材摘要',
            script_style VARCHAR(64) NULL COMMENT '文案风格',
            duration_seconds INT NOT NULL DEFAULT 180 COMMENT '目标时长（秒）',
            render_plan JSON NOT NULL COMMENT '渲染计划',
            output_url TEXT NULL COMMENT '第 05 步融合成片地址',
            current_step VARCHAR(32) NOT NULL DEFAULT 'product' COMMENT '当前停留步骤：product/review/avatar/layout/preview',
            status VARCHAR(32) NOT NULL DEFAULT 'draft' COMMENT '草稿状态',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            KEY idx_avatar_draft_clip_user_updated (user_id, updated_at),
            KEY idx_avatar_draft_clip_user_status (user_id, status),
            KEY idx_avatar_draft_clip_user_step (user_id, current_step),
            KEY idx_avatar_draft_clip_product (selected_product_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='视频剪辑数字人草稿表'
        """
        with self.session_scope() as session:
            session.execute(text(ddl))

    def create(self, record: AvatarClipDraftRecord) -> AvatarClipDraftRecord:
        with self.session_scope() as session:
            model = AvatarClipDraftModel(**self._model_values(record))
            session.add(model)
            session.flush()
            return AvatarClipDraftRecord.from_model(model)

    def get(self, draft_id: str, user_id: int) -> AvatarClipDraftRecord | None:
        with self.session_scope() as session:
            stmt = select(AvatarClipDraftModel).where(
                AvatarClipDraftModel.draft_id == draft_id,
                AvatarClipDraftModel.user_id == user_id,
            )
            model = session.scalar(stmt)
            return AvatarClipDraftRecord.from_model(model) if model else None

    def list_by_user(self, user_id: int, *, limit: int = 20, offset: int = 0) -> list[AvatarClipDraftRecord]:
        with self.session_scope() as session:
            stmt = (
                select(AvatarClipDraftModel)
                .where(AvatarClipDraftModel.user_id == user_id)
                .order_by(AvatarClipDraftModel.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )
            models = session.scalars(stmt).all()
            return [AvatarClipDraftRecord.from_model(model) for model in models]

    def update(self, record: AvatarClipDraftRecord) -> AvatarClipDraftRecord:
        with self.session_scope() as session:
            model = session.get(AvatarClipDraftModel, record.draft_id)
            if model is None or model.user_id != record.user_id:
                raise ValueError(f"Avatar clip draft {record.draft_id} not found")
            for key, value in self._model_values(record).items():
                if key in {"draft_id", "user_id"}:
                    continue
                setattr(model, key, value)
            session.flush()
            return AvatarClipDraftRecord.from_model(model)

    def delete(self, draft_id: str, user_id: int) -> bool:
        with self.session_scope() as session:
            stmt = select(AvatarClipDraftModel).where(
                AvatarClipDraftModel.draft_id == draft_id,
                AvatarClipDraftModel.user_id == user_id,
            )
            model = session.scalar(stmt)
            if model is None:
                return False
            session.delete(model)
            session.flush()
            return True

    @staticmethod
    def _model_values(record: AvatarClipDraftRecord) -> dict[str, Any]:
        return {
            "draft_id": record.draft_id,
            "user_id": record.user_id,
            "title": record.title,
            "source_url": record.source_url,
            "platform": record.platform,
            "content_id": record.content_id,
            "content_info": record.content_info,
            "transcript": record.transcript,
            "extracted_copy": record.extracted_copy,
            "rewrite_instruction": record.rewrite_instruction,
            "rewritten_copy": record.rewritten_copy,
            "voice_params": record.voice_params,
            "digital_human_params": record.digital_human_params,
            "clip_params": record.clip_params,
            "selected_product_id": record.selected_product_id,
            "selected_product_profile": record.selected_product_profile,
            "product_assets": record.product_assets,
            "selected_selling_point_ids": record.selected_selling_point_ids,
            "selected_clip_asset_ids": record.selected_clip_asset_ids,
            "selected_reference_asset_ids": record.selected_reference_asset_ids,
            "review_units": record.review_units,
            "delete_segments": record.delete_segments,
            "cut_summary": record.cut_summary,
            "clipped_video_url": record.clipped_video_url,
            "clipped_audio_url": record.clipped_audio_url,
            "avatar_source_mode": record.avatar_source_mode,
            "avatar_image_url": record.avatar_image_url,
            "avatar_video_url": record.avatar_video_url,
            "generated_avatar_video_url": record.generated_avatar_video_url,
            "generated_avatar_source_url": record.generated_avatar_source_url,
            "avatar_task_id": record.avatar_task_id,
            "avatar_task_status": record.avatar_task_status,
            "overlay_position": record.overlay_position,
            "overlay_size_percent": record.overlay_size_percent,
            "overlay_shape": record.overlay_shape,
            "overlay_border": int(record.overlay_border),
            "overlay_shadow": int(record.overlay_shadow),
            "overlay_plate": int(record.overlay_plate),
            "material_summary": record.material_summary,
            "script_style": record.script_style,
            "duration_seconds": record.duration_seconds,
            "render_plan": record.render_plan,
            "output_url": record.output_url,
            "current_step": record.current_step,
            "status": record.status,
        }

