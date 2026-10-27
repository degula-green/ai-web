from __future__ import annotations

from app.core.exceptions import ContractError
from app.db.repositories.avatar_clip_draft_repository import AvatarClipDraftRecord, AvatarClipDraftRepository
from app.db.repositories.avatar_draft_repository import AvatarDraftRecord, AvatarDraftRepository
from app.db.repositories.creation_draft_repository import CreationDraftRecord, CreationDraftRepository
from app.schemas.avatar_clip_draft import (
    AvatarClipDraftCreateRequest,
    AvatarClipDraftRead,
    AvatarClipDraftUpdateRequest,
)
from app.utils.ids import generate_id


CLIP_SCENE_NAME = "视频剪辑数字人"


class AvatarClipDraftService:
    def __init__(
        self,
        *,
        repository: AvatarClipDraftRepository,
        avatar_repository: AvatarDraftRepository,
        creation_repository: CreationDraftRepository,
    ) -> None:
        self.repository = repository
        self.avatar_repository = avatar_repository
        self.creation_repository = creation_repository

    def initialize(self) -> None:
        self.repository.ensure_table()

    def create(self, *, user_id: int, payload: AvatarClipDraftCreateRequest) -> AvatarClipDraftRead:
        record = self._record_from_payload(
            AvatarClipDraftRecord(draft_id=generate_id("draft"), user_id=user_id),
            payload,
        )
        saved = self.repository.create(record)
        self._sync_avatar_draft(saved)
        self._sync_creation_draft(saved)
        return self._to_read(saved)

    def get(self, *, user_id: int, draft_id: str) -> AvatarClipDraftRead:
        record = self.repository.get(draft_id, user_id)
        if record is None:
            raise ContractError("avatar clip draft not found", status_code=404)
        return self._to_read(record)

    def list_by_user(self, *, user_id: int, limit: int = 20, offset: int = 0) -> list[AvatarClipDraftRead]:
        return [self._to_read(item) for item in self.repository.list_by_user(user_id, limit=limit, offset=offset)]

    def update(self, *, user_id: int, draft_id: str, payload: AvatarClipDraftUpdateRequest) -> AvatarClipDraftRead:
        existing = self.repository.get(draft_id, user_id)
        if existing is None:
            raise ContractError("avatar clip draft not found", status_code=404)
        record = self._record_from_update(existing, payload)
        saved = self.repository.update(record)
        self._sync_avatar_draft(saved)
        self._sync_creation_draft(saved)
        return self._to_read(saved)

    def delete(self, *, user_id: int, draft_id: str) -> None:
        deleted = self.repository.delete(draft_id, user_id)
        if not deleted:
            raise ContractError("avatar clip draft not found", status_code=404)
        self.avatar_repository.soft_delete(draft_id, user_id)
        self.creation_repository.delete(draft_id, user_id)

    def sync_from_creation_draft_id(self, *, user_id: int, draft_id: str) -> AvatarClipDraftRead:
        creation_record = self.creation_repository.get(draft_id, user_id)
        if creation_record is None:
            raise ContractError("creation draft not found", status_code=404)
        if not self._is_clip_creation_draft(creation_record):
            raise ContractError("draft is not a clip draft", status_code=409)
        saved = self._upsert_from_creation_draft(creation_record)
        self._sync_avatar_draft(saved)
        return self._to_read(saved)

    def _sync_avatar_draft(self, record: AvatarClipDraftRecord) -> None:
        self.avatar_repository.upsert(
            AvatarDraftRecord(
                draft_id=record.draft_id,
                user_id=record.user_id,
                scene_code="clip",
                title=record.title,
                status=record.status or "draft",
                current_step_code=record.current_step or self._resolve_current_step_code(record),
                progress=self._resolve_progress(record),
                is_deleted=0,
            )
        )

    def _sync_creation_draft(self, record: AvatarClipDraftRecord) -> None:
        creation_record = self._to_creation_record(record)
        existing = self.creation_repository.get(record.draft_id, record.user_id)
        if existing is None:
            self.creation_repository.create(creation_record)
        else:
            self.creation_repository.update(creation_record)

    def _upsert_from_creation_draft(self, creation_record: CreationDraftRecord) -> AvatarClipDraftRecord:
        clip_record = self._from_creation_draft(creation_record)
        existing = self.repository.get(creation_record.draft_id, creation_record.user_id)
        if existing is None:
            return self.repository.create(clip_record)
        return self.repository.update(clip_record)

    @staticmethod
    def _record_from_payload(base: AvatarClipDraftRecord, payload: AvatarClipDraftCreateRequest) -> AvatarClipDraftRecord:
        for key, value in payload.model_dump().items():
            setattr(base, key, value)
        return base

    @staticmethod
    def _record_from_update(existing: AvatarClipDraftRecord, payload: AvatarClipDraftUpdateRequest) -> AvatarClipDraftRecord:
        data = payload.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(existing, key, value)
        return existing

    @staticmethod
    def _is_clip_creation_draft(record: CreationDraftRecord) -> bool:
        digital = record.digital_human_params or {}
        content_info = record.content_info or {}
        purpose = str(digital.get("video_purpose") or content_info.get("purpose_scene") or "").strip()
        if purpose == CLIP_SCENE_NAME:
            return True
        if purpose:
            return False
        return AvatarClipDraftService._has_clip_scene_signals(record)

    @staticmethod
    def _has_clip_scene_signals(record: CreationDraftRecord) -> bool:
        content_info = record.content_info or {}
        clip_params = record.clip_params or {}
        return bool(
            content_info.get("selected_product_id")
            or content_info.get("selected_clip_asset_ids")
            or clip_params.get("review_units")
            or clip_params.get("delete_segments")
            or clip_params.get("generated_avatar_video_url")
            or clip_params.get("merged_output_url")
            or clip_params.get("clipped_video_url")
            or clip_params.get("output_url")
        )

    @staticmethod
    def _from_creation_draft(record: CreationDraftRecord) -> AvatarClipDraftRecord:
        content_info = record.content_info or {}
        clip_params = record.clip_params or {}
        digital = record.digital_human_params or {}
        overlay = clip_params.get("overlay") if isinstance(clip_params.get("overlay"), dict) else {}
        cut_summary = clip_params.get("cut_summary") if isinstance(clip_params.get("cut_summary"), dict) else {}
        return AvatarClipDraftRecord(
            draft_id=record.draft_id,
            user_id=record.user_id,
            title=record.title,
            source_url=record.source_url,
            platform=record.platform,
            content_id=record.content_id,
            content_info=content_info,
            transcript=record.transcript,
            extracted_copy=record.extracted_copy,
            rewrite_instruction=record.rewrite_instruction,
            rewritten_copy=record.rewritten_copy,
            voice_params=record.voice_params,
            digital_human_params=digital,
            clip_params=clip_params,
            selected_product_id=str(content_info.get("selected_product_id") or record.content_id or "") or None,
            selected_product_profile=content_info.get("selected_product_profile") or {},
            product_assets=content_info.get("product_assets") or [],
            selected_selling_point_ids=[str(item) for item in (content_info.get("selected_selling_point_ids") or [])],
            selected_clip_asset_ids=[str(item) for item in (content_info.get("selected_clip_asset_ids") or [])],
            selected_reference_asset_ids=[str(item) for item in (content_info.get("selected_reference_asset_ids") or [])],
            review_units=clip_params.get("review_units") or [],
            delete_segments=clip_params.get("delete_segments") or [],
            cut_summary=cut_summary,
            clipped_video_url=AvatarClipDraftService._first_text(clip_params, "clipped_video_url", "clipped_video_playback_path"),
            clipped_audio_url=AvatarClipDraftService._first_text(clip_params, "clipped_audio_url", "clipped_audio_playback_path"),
            avatar_source_mode=str(digital.get("avatar_source_mode") or "image"),
            avatar_image_url=AvatarClipDraftService._first_text(digital, "avatar_image_url", "image_url"),
            avatar_video_url=AvatarClipDraftService._first_text(digital, "avatar_video_url", "video_url"),
            generated_avatar_video_url=AvatarClipDraftService._first_text(digital, "generated_avatar_video_url"),
            generated_avatar_source_url=AvatarClipDraftService._first_text(digital, "generated_avatar_source_url"),
            avatar_task_id=AvatarClipDraftService._first_text(digital, "avatar_task_id"),
            avatar_task_status=AvatarClipDraftService._first_text(digital, "avatar_task_status"),
            overlay_position=str(overlay.get("position") or "bottom-right"),
            overlay_size_percent=int(overlay.get("size_percent") or 30),
            overlay_shape=str(overlay.get("shape") or "square"),
            overlay_border=bool(overlay.get("border")),
            overlay_shadow=bool(overlay.get("shadow")),
            overlay_plate=bool(overlay.get("plate")),
            material_summary=str(content_info.get("material_summary") or "") or None,
            script_style=str(content_info.get("script_style") or content_info.get("style") or "") or None,
            duration_seconds=max(1, int(content_info.get("duration_seconds") or 180)),
            render_plan=clip_params.get("render_plan") if isinstance(clip_params.get("render_plan"), list) else [],
            output_url=AvatarClipDraftService._first_text(clip_params, "merged_output_url", "output_url", "playback_path"),
            current_step=str(clip_params.get("current_step") or "product"),
            status=record.status or "draft",
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def _to_creation_record(record: AvatarClipDraftRecord) -> CreationDraftRecord:
        content_info = dict(record.content_info or {})
        digital_human_params = dict(record.digital_human_params or {})
        clip_params = AvatarClipDraftService._merge_clip_params(record)
        content_info.update(
            {
                "selected_product_id": record.selected_product_id,
                "selected_product_profile": record.selected_product_profile,
                "product_assets": record.product_assets,
                "selected_selling_point_ids": record.selected_selling_point_ids,
                "selected_clip_asset_ids": record.selected_clip_asset_ids,
                "selected_reference_asset_ids": record.selected_reference_asset_ids,
                "material_summary": record.material_summary,
                "script_style": record.script_style,
                "duration_seconds": record.duration_seconds,
                "purpose_scene": CLIP_SCENE_NAME,
            }
        )
        digital_human_params.update(
            {
                "video_purpose": CLIP_SCENE_NAME,
                "avatar_source_mode": record.avatar_source_mode,
                "avatar_image_url": record.avatar_image_url,
                "avatar_video_url": record.avatar_video_url,
                "generated_avatar_video_url": record.generated_avatar_video_url,
                "generated_avatar_source_url": record.generated_avatar_source_url,
                "avatar_task_id": record.avatar_task_id,
                "avatar_task_status": record.avatar_task_status,
            }
        )

        return CreationDraftRecord(
            draft_id=record.draft_id,
            user_id=record.user_id,
            title=record.title,
            source_url=record.source_url,
            platform=record.platform,
            content_id=record.content_id,
            content_info=content_info,
            transcript=record.transcript,
            extracted_copy=record.extracted_copy,
            rewrite_instruction=record.rewrite_instruction,
            rewritten_copy=record.rewritten_copy,
            voice_params=record.voice_params,
            digital_human_params=digital_human_params,
            clip_params=clip_params,
            status=record.status,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def _resolve_current_step_code(record: AvatarClipDraftRecord) -> str:
        if record.output_url:
            return "preview"
        if record.generated_avatar_video_url:
            return "layout"
        if record.clipped_video_url or record.review_units:
            return "avatar"
        if record.selected_clip_asset_ids:
            return "review"
        return "product"

    @staticmethod
    def _resolve_progress(record: AvatarClipDraftRecord) -> int:
        step = record.current_step or AvatarClipDraftService._resolve_current_step_code(record)
        return {
            "product": 15,
            "review": 35,
            "avatar": 60,
            "layout": 80,
            "preview": 100,
        }.get(step, 15)

    @staticmethod
    def _to_read(record: AvatarClipDraftRecord) -> AvatarClipDraftRead:
        clip_params = AvatarClipDraftService._merge_clip_params(record)
        return AvatarClipDraftRead(
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
            clip_params=clip_params,
            selected_product_id=record.selected_product_id,
            selected_product_profile=record.selected_product_profile,
            product_assets=record.product_assets,
            selected_selling_point_ids=record.selected_selling_point_ids,
            selected_clip_asset_ids=record.selected_clip_asset_ids,
            selected_reference_asset_ids=record.selected_reference_asset_ids,
            review_units=record.review_units,
            delete_segments=record.delete_segments,
            cut_summary=record.cut_summary,
            clipped_video_url=record.clipped_video_url,
            clipped_audio_url=record.clipped_audio_url,
            avatar_source_mode=record.avatar_source_mode,
            avatar_image_url=record.avatar_image_url,
            avatar_video_url=record.avatar_video_url,
            generated_avatar_video_url=record.generated_avatar_video_url,
            generated_avatar_source_url=record.generated_avatar_source_url,
            avatar_task_id=record.avatar_task_id,
            avatar_task_status=record.avatar_task_status,
            overlay_position=record.overlay_position,
            overlay_size_percent=record.overlay_size_percent,
            overlay_shape=record.overlay_shape,
            overlay_border=record.overlay_border,
            overlay_shadow=record.overlay_shadow,
            overlay_plate=record.overlay_plate,
            material_summary=record.material_summary,
            script_style=record.script_style,
            duration_seconds=record.duration_seconds,
            render_plan=record.render_plan,
            output_url=record.output_url,
            current_step=record.current_step,
            status=record.status,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def _merge_clip_params(record: AvatarClipDraftRecord) -> dict[str, object]:
        clip_params: dict[str, object] = dict(record.clip_params or {})
        clip_params.update(
            {
                "review_units": record.review_units,
                "delete_segments": record.delete_segments,
                "cut_summary": record.cut_summary,
                "clipped_video_url": record.clipped_video_url,
                "clipped_audio_url": record.clipped_audio_url,
                "overlay": {
                    "position": record.overlay_position,
                    "size_percent": record.overlay_size_percent,
                    "shape": record.overlay_shape,
                    "border": record.overlay_border,
                    "shadow": record.overlay_shadow,
                    "plate": record.overlay_plate,
                },
                "render_plan": record.render_plan,
                "output_url": record.output_url,
                "merged_output_url": record.output_url,
                "current_step": record.current_step,
            }
        )
        return {key: value for key, value in clip_params.items() if value not in (None, "")}

    @staticmethod
    def _first_text(source: dict[str, object], *keys: str) -> str | None:
        for key in keys:
            value = source.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None
