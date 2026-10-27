from __future__ import annotations

from app.core.exceptions import ContractError
from app.db.repositories.avatar_draft_repository import AvatarDraftRecord, AvatarDraftRepository
from app.db.repositories.avatar_model_draft_repository import AvatarModelDraftRecord, AvatarModelDraftRepository
from app.db.repositories.creation_draft_repository import CreationDraftRecord, CreationDraftRepository
from app.schemas.avatar_model_draft import (
    AvatarModelDraftCreateRequest,
    AvatarModelDraftRead,
    AvatarModelDraftUpdateRequest,
)
from app.utils.ids import generate_id


class AvatarModelDraftService:
    def __init__(
        self,
        *,
        repository: AvatarModelDraftRepository,
        avatar_repository: AvatarDraftRepository,
        creation_repository: CreationDraftRepository | None = None,
    ) -> None:
        self.repository = repository
        self.avatar_repository = avatar_repository
        self.creation_repository = creation_repository

    def initialize(self) -> None:
        self.repository.ensure_table()
        self._backfill_from_creation_drafts()

    def create(self, *, user_id: int, payload: AvatarModelDraftCreateRequest) -> AvatarModelDraftRead:
        record = AvatarModelDraftRecord(
            draft_id=generate_id("draft"),
            user_id=user_id,
            title=payload.title,
            product_keyword=payload.product_keyword,
            selected_product_id=payload.selected_product_id,
            selected_product_profile=payload.selected_product_profile,
            product_assets=payload.product_assets,
            selected_white_image_id=payload.selected_white_image_id,
            selected_wear_image_id=payload.selected_wear_image_id,
            model_image_url=payload.model_image_url,
            scene_image_url=payload.scene_image_url,
            image_count=payload.image_count,
            aspect_ratio=payload.aspect_ratio,
            extra_requirements=payload.extra_requirements,
            gallery_task_id=payload.gallery_task_id,
            gallery_task_status=payload.gallery_task_status,
            gallery_images=payload.gallery_images,
            status=payload.status,
        )
        saved = self.repository.create(record)
        self._sync_avatar_draft(saved)
        return self._to_read(saved)

    def get(self, *, user_id: int, draft_id: str) -> AvatarModelDraftRead:
        record = self.repository.get(draft_id, user_id)
        if record is None:
            raise ContractError("模特数字人草稿不存在", status_code=404)
        return self._to_read(record)

    def list_by_user(self, *, user_id: int, limit: int = 20, offset: int = 0) -> list[AvatarModelDraftRead]:
        return [self._to_read(item) for item in self.repository.list_by_user(user_id, limit=limit, offset=offset)]

    def update(self, *, user_id: int, draft_id: str, payload: AvatarModelDraftUpdateRequest) -> AvatarModelDraftRead:
        existing = self.repository.get(draft_id, user_id)
        if existing is None:
            raise ContractError("模特数字人草稿不存在", status_code=404)
        record = AvatarModelDraftRecord(
            draft_id=existing.draft_id,
            user_id=existing.user_id,
            title=payload.title if payload.title is not None else existing.title,
            product_keyword=payload.product_keyword if payload.product_keyword is not None else existing.product_keyword,
            selected_product_id=payload.selected_product_id
            if payload.selected_product_id is not None
            else existing.selected_product_id,
            selected_product_profile=payload.selected_product_profile
            if payload.selected_product_profile is not None
            else existing.selected_product_profile,
            product_assets=payload.product_assets if payload.product_assets is not None else existing.product_assets,
            selected_white_image_id=payload.selected_white_image_id
            if payload.selected_white_image_id is not None
            else existing.selected_white_image_id,
            selected_wear_image_id=payload.selected_wear_image_id
            if payload.selected_wear_image_id is not None
            else existing.selected_wear_image_id,
            model_image_url=payload.model_image_url if payload.model_image_url is not None else existing.model_image_url,
            scene_image_url=payload.scene_image_url if payload.scene_image_url is not None else existing.scene_image_url,
            image_count=payload.image_count if payload.image_count is not None else existing.image_count,
            aspect_ratio=payload.aspect_ratio if payload.aspect_ratio is not None else existing.aspect_ratio,
            extra_requirements=payload.extra_requirements
            if payload.extra_requirements is not None
            else existing.extra_requirements,
            gallery_task_id=payload.gallery_task_id if payload.gallery_task_id is not None else existing.gallery_task_id,
            gallery_task_status=payload.gallery_task_status
            if payload.gallery_task_status is not None
            else existing.gallery_task_status,
            gallery_images=payload.gallery_images if payload.gallery_images is not None else existing.gallery_images,
            status=payload.status if payload.status is not None else existing.status,
            created_at=existing.created_at,
            updated_at=existing.updated_at,
        )
        saved = self.repository.update(record)
        self._sync_avatar_draft(saved)
        return self._to_read(saved)

    def delete(self, *, user_id: int, draft_id: str) -> None:
        deleted = self.repository.delete(draft_id, user_id)
        if not deleted:
            raise ContractError("模特数字人草稿不存在", status_code=404)
        self.avatar_repository.soft_delete(draft_id, user_id)

    def _sync_avatar_draft(self, record: AvatarModelDraftRecord) -> None:
        self.avatar_repository.upsert(
            AvatarDraftRecord(
                draft_id=record.draft_id,
                user_id=record.user_id,
                scene_code="model",
                title=record.title,
                status=record.status or "draft",
                current_step_code="completed" if record.status == "gallery_generated" else "model_gallery",
                progress=100 if record.status == "gallery_generated" else 40,
                is_deleted=0,
            )
        )

    def _backfill_from_creation_drafts(self) -> None:
        if self.creation_repository is None:
            return
        for creation_record in self.creation_repository.list_all():
            if not self._is_model_creation_draft(creation_record):
                continue
            existing = self.repository.get(creation_record.draft_id, creation_record.user_id)
            if existing is not None:
                self._sync_avatar_draft(existing)
                continue
            record = self._from_creation_draft(creation_record)
            saved = self.repository.create(record)
            self._sync_avatar_draft(saved)

    @staticmethod
    def _is_model_creation_draft(record: CreationDraftRecord) -> bool:
        digital = record.digital_human_params or {}
        content_info = record.content_info or {}
        purpose = str(digital.get("video_purpose") or content_info.get("purpose_scene") or "").strip()
        has_model_scene = isinstance(digital.get("model_scene"), dict) and bool(digital.get("model_scene"))
        if purpose:
            return purpose == "模特数字人"
        return has_model_scene or str(record.status or "").strip().lower() == "gallery_generated"

    @staticmethod
    def _from_creation_draft(record: CreationDraftRecord) -> AvatarModelDraftRecord:
        digital = record.digital_human_params or {}
        content_info = record.content_info or {}
        model_scene = digital.get("model_scene") if isinstance(digital.get("model_scene"), dict) else {}
        return AvatarModelDraftRecord(
            draft_id=record.draft_id,
            user_id=record.user_id,
            title=record.title,
            product_keyword=str(content_info.get("product_keyword") or "") or None,
            selected_product_id=str(model_scene.get("selected_product_id") or record.content_id or "") or None,
            selected_product_profile=model_scene.get("selected_product_profile") or {},
            product_assets=model_scene.get("product_assets") or content_info.get("product_assets") or [],
            selected_white_image_id=str(model_scene.get("selected_white_image_id") or "") or None,
            selected_wear_image_id=str(model_scene.get("selected_wear_image_id") or "") or None,
            model_image_url=str(model_scene.get("model_image_url") or digital.get("image_url") or "") or None,
            scene_image_url=str(model_scene.get("scene_image_url") or "") or None,
            image_count=int(model_scene.get("image_count") or 8),
            aspect_ratio=str(model_scene.get("aspect_ratio") or "3:4"),
            extra_requirements=str(model_scene.get("extra_requirements") or record.rewrite_instruction or "") or None,
            gallery_task_id=str(model_scene.get("gallery_task_id") or digital.get("task_id") or "") or None,
            gallery_task_status=str(model_scene.get("gallery_task_status") or digital.get("task_status") or "") or None,
            gallery_images=model_scene.get("gallery_images") or [],
            status=record.status or "draft",
        )

    @staticmethod
    def _to_read(record: AvatarModelDraftRecord) -> AvatarModelDraftRead:
        return AvatarModelDraftRead(
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
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
