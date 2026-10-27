from __future__ import annotations

from app.core.exceptions import ContractError
from app.db.repositories.avatar_draft_repository import AvatarDraftRepository
from app.db.repositories.creation_draft_repository import CreationDraftRecord, CreationDraftRepository
from app.schemas.creation_draft import (
    CreationDraftCreateRequest,
    CreationDraftRead,
    CreationDraftUpdateRequest,
    DigitalHumanAssetUpdateRequest,
)
from app.services.avatar_draft_service import AvatarDraftService
from app.utils.ids import generate_id


class CreationDraftService:
    def __init__(
        self,
        *,
        repository: CreationDraftRepository,
        avatar_repository: AvatarDraftRepository | None = None,
    ) -> None:
        self.repository = repository
        self.avatar_repository = avatar_repository

    def initialize(self) -> None:
        self.repository.ensure_table()
        self._backfill_avatar_drafts()

    def create(self, *, user_id: int, payload: CreationDraftCreateRequest) -> CreationDraftRead:
        record = CreationDraftRecord(
            draft_id=generate_id("draft"),
            user_id=user_id,
            title=payload.title,
            source_url=payload.source_url,
            platform=payload.platform,
            content_id=payload.content_id,
            content_info=payload.content_info,
            transcript=payload.transcript,
            extracted_copy=payload.extracted_copy,
            rewrite_instruction=payload.rewrite_instruction,
            rewritten_copy=payload.rewritten_copy,
            voice_params=payload.voice_params,
            digital_human_params=payload.digital_human_params,
            clip_params=payload.clip_params,
            status=payload.status,
        )
        saved = self.repository.create(record)
        self._sync_avatar_draft(saved)
        return self._to_read(saved)

    def get(self, *, user_id: int, draft_id: str) -> CreationDraftRead:
        record = self.repository.get(draft_id, user_id)
        if record is None:
            raise ContractError("创作草稿不存在", status_code=404)
        return self._to_read(record)

    def list_by_user(self, *, user_id: int, limit: int = 20, offset: int = 0) -> list[CreationDraftRead]:
        return [self._to_read(item) for item in self.repository.list_by_user(user_id, limit=limit, offset=offset)]

    def update(self, *, user_id: int, draft_id: str, payload: CreationDraftUpdateRequest) -> CreationDraftRead:
        existing = self.repository.get(draft_id, user_id)
        if existing is None:
            raise ContractError("创作草稿不存在", status_code=404)

        self._ensure_scene_not_changed(existing=existing, payload=payload)

        record = CreationDraftRecord(
            draft_id=existing.draft_id,
            user_id=existing.user_id,
            title=payload.title if payload.title is not None else existing.title,
            source_url=payload.source_url if payload.source_url is not None else existing.source_url,
            platform=payload.platform if payload.platform is not None else existing.platform,
            content_id=payload.content_id if payload.content_id is not None else existing.content_id,
            content_info=payload.content_info if payload.content_info is not None else existing.content_info,
            transcript=payload.transcript if payload.transcript is not None else existing.transcript,
            extracted_copy=payload.extracted_copy if payload.extracted_copy is not None else existing.extracted_copy,
            rewrite_instruction=payload.rewrite_instruction
            if payload.rewrite_instruction is not None
            else existing.rewrite_instruction,
            rewritten_copy=payload.rewritten_copy if payload.rewritten_copy is not None else existing.rewritten_copy,
            voice_params=payload.voice_params if payload.voice_params is not None else existing.voice_params,
            digital_human_params=payload.digital_human_params
            if payload.digital_human_params is not None
            else existing.digital_human_params,
            clip_params=payload.clip_params if payload.clip_params is not None else existing.clip_params,
            status=payload.status if payload.status is not None else existing.status,
            created_at=existing.created_at,
            updated_at=existing.updated_at,
        )
        saved = self.repository.update(record)
        self._sync_avatar_draft(saved)
        return self._to_read(saved)

    def update_digital_human_asset(
        self,
        *,
        user_id: int,
        draft_id: str,
        payload: DigitalHumanAssetUpdateRequest,
    ) -> CreationDraftRead:
        existing = self.repository.get(draft_id, user_id)
        if existing is None:
            raise ContractError("创作草稿不存在", status_code=404)

        digital = dict(existing.digital_human_params or {})
        media_type = payload.media_type.strip().lower()
        url = payload.file_url.strip()

        if media_type == "image":
            digital["image_url"] = url
            digital["human_type"] = payload.human_type or "image"
        else:
            digital["video_url"] = url
            digital["human_type"] = payload.human_type or "video"

        record = CreationDraftRecord(
            draft_id=existing.draft_id,
            user_id=existing.user_id,
            title=existing.title,
            source_url=existing.source_url,
            platform=existing.platform,
            content_id=existing.content_id,
            content_info=existing.content_info,
            transcript=existing.transcript,
            extracted_copy=existing.extracted_copy,
            rewrite_instruction=existing.rewrite_instruction,
            rewritten_copy=existing.rewritten_copy,
            voice_params=existing.voice_params,
            digital_human_params=digital,
            clip_params=existing.clip_params,
            status=existing.status,
            created_at=existing.created_at,
            updated_at=existing.updated_at,
        )
        saved = self.repository.update(record)
        self._sync_avatar_draft(saved)
        return self._to_read(saved)

    def delete(self, *, user_id: int, draft_id: str) -> None:
        deleted = self.repository.delete(draft_id, user_id)
        if not deleted:
            raise ContractError("创作草稿不存在", status_code=404)
        if self.avatar_repository is not None:
            self.avatar_repository.soft_delete(draft_id, user_id)

    def _sync_avatar_draft(self, record: CreationDraftRecord) -> None:
        if self.avatar_repository is None:
            return
        AvatarDraftService(repository=self.avatar_repository).sync_from_creation_draft(record)

    def _backfill_avatar_drafts(self) -> None:
        if self.avatar_repository is None:
            return
        avatar_service = AvatarDraftService(repository=self.avatar_repository)
        for record in self.repository.list_all():
            avatar_service.sync_from_creation_draft(record)

    @staticmethod
    def _extract_explicit_scene_from_payload(payload: CreationDraftUpdateRequest) -> str | None:
        digital = payload.digital_human_params or {}
        content_info = payload.content_info or {}
        raw_scene = str(digital.get("video_purpose") or content_info.get("purpose_scene") or "").strip()
        return raw_scene or None

    def _ensure_scene_not_changed(
        self,
        *,
        existing: CreationDraftRecord,
        payload: CreationDraftUpdateRequest,
    ) -> None:
        existing_scene = AvatarDraftService.extract_explicit_scene(existing)
        payload_scene = self._extract_explicit_scene_from_payload(payload)
        if existing_scene and payload_scene and existing_scene != payload_scene:
            raise ContractError(
                f"draft scene mismatch: existing={existing_scene}, payload={payload_scene}",
                status_code=409,
            )

    @staticmethod
    def _to_read(record: CreationDraftRecord) -> CreationDraftRead:
        return CreationDraftRead(
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
            status=record.status,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
