from __future__ import annotations

from typing import Any

from app.core.exceptions import ContractError
from app.db.repositories.video_edit_template_repository import (
    VideoEditTemplateRecord,
    VideoEditTemplateRepository,
)
from app.schemas.video_edit_template import (
    VideoEditTemplateCreateRequest,
    VideoEditTemplateListResponse,
    VideoEditTemplateRead,
    VideoEditTemplateUpdateRequest,
)


class VideoEditTemplateService:
    def __init__(self, *, repository: VideoEditTemplateRepository) -> None:
        self.repository = repository

    def initialize(self) -> None:
        self.repository.ensure_table()

    def list_available(
        self,
        *,
        user_id: int,
        template_type: str | None = None,
        scene_code: str | None = None,
    ) -> VideoEditTemplateListResponse:
        records = self.repository.list_available(
            user_id=user_id,
            template_type=self._normalize_optional(template_type),
            scene_code=self._normalize_optional(scene_code),
        )
        return VideoEditTemplateListResponse(items=[self._to_read(item) for item in records])

    def create_user_template(self, *, user_id: int, payload: VideoEditTemplateCreateRequest) -> VideoEditTemplateRead:
        if not payload.render_config:
            raise ContractError("模板渲染配置不能为空", status_code=400)
        record = self.repository.create_user_template(
            user_id=user_id,
            name=payload.name.strip(),
            description=(payload.description or "").strip(),
            template_type=payload.template_type.strip() or "clip",
            scene_code=payload.scene_code.strip() or "digital_human_talk",
            render_config=payload.render_config,
            editor_config=payload.editor_config,
            thumbnail_url=(payload.thumbnail_url or "").strip() or None,
        )
        return self._to_read(record)

    def update_user_template(
        self,
        *,
        user_id: int,
        template_id: int,
        payload: VideoEditTemplateUpdateRequest,
    ) -> VideoEditTemplateRead:
        values: dict[str, Any] = {}
        if payload.name is not None:
            values["name"] = payload.name.strip()
        if payload.description is not None:
            values["description"] = payload.description.strip()
        if payload.template_type is not None:
            values["template_type"] = payload.template_type.strip() or "clip"
        if payload.scene_code is not None:
            values["scene_code"] = payload.scene_code.strip() or "digital_human_talk"
        if payload.render_config is not None:
            if not payload.render_config:
                raise ContractError("模板渲染配置不能为空", status_code=400)
            values["render_config"] = payload.render_config
        if payload.editor_config is not None:
            values["editor_config"] = payload.editor_config
        if payload.thumbnail_url is not None:
            values["thumbnail_url"] = payload.thumbnail_url.strip() or None
        if payload.status is not None:
            values["status"] = payload.status

        if not values:
            raise ContractError("没有可更新的模板字段", status_code=400)

        record = self.repository.update_user_template(user_id=user_id, template_id=template_id, values=values)
        if record is None:
            raise ContractError("模板不存在或无权限修改", status_code=404)
        return self._to_read(record)

    def delete_user_template(self, *, user_id: int, template_id: int) -> None:
        if not self.repository.soft_delete_user_template(user_id=user_id, template_id=template_id):
            raise ContractError("模板不存在或无权限删除", status_code=404)

    @staticmethod
    def _normalize_optional(value: str | None) -> str | None:
        normalized = (value or "").strip()
        return normalized or None

    @staticmethod
    def _to_read(record: VideoEditTemplateRecord) -> VideoEditTemplateRead:
        return VideoEditTemplateRead(
            id=record.id,
            user_id=record.user_id,
            name=record.name,
            description=record.description,
            template_type=record.template_type,
            scene_code=record.scene_code,
            render_config=record.render_config,
            editor_config=record.editor_config,
            thumbnail_url=record.thumbnail_url,
            source_type=record.source_type,
            status=record.status,
            sort_order=record.sort_order,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
