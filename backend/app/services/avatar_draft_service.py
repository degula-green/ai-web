from __future__ import annotations

from app.core.exceptions import ContractError
from app.db.repositories.avatar_draft_repository import AvatarDraftRecord, AvatarDraftRepository
from app.db.repositories.creation_draft_repository import CreationDraftRecord
from app.schemas.avatar_draft import AvatarDraftRead


SCENE_NAME_TO_CODE = {
    "口播数字人": "talk",
    "卖货数字人": "sales",
    "带货数字人": "sales",
    "产品介绍数字人": "product",
    "模特数字人": "model",
    "视频剪辑数字人": "clip",
}


class AvatarDraftService:
    def __init__(self, *, repository: AvatarDraftRepository) -> None:
        self.repository = repository

    def initialize(self) -> None:
        self.repository.ensure_table()

    def get(self, *, user_id: int, draft_id: str) -> AvatarDraftRead:
        record = self.repository.get(draft_id, user_id)
        if record is None:
            raise ContractError("数字人草稿不存在", status_code=404)
        return self._to_read(record)

    def list_by_user(
        self,
        *,
        user_id: int,
        scene_code: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[AvatarDraftRead]:
        return [
            self._to_read(item)
            for item in self.repository.list_by_user(user_id, scene_code=scene_code, limit=limit, offset=offset)
        ]

    def sync_from_creation_draft(self, record: CreationDraftRecord) -> AvatarDraftRead:
        saved = self.repository.upsert(
            AvatarDraftRecord(
                draft_id=record.draft_id,
                user_id=record.user_id,
                scene_code=self.resolve_scene_code(record),
                title=record.title,
                status=record.status or "draft",
                current_step_code=self.resolve_current_step_code(record.status),
                progress=self.resolve_progress(record.status),
                is_deleted=0,
            )
        )
        return self._to_read(saved)

    def soft_delete(self, *, user_id: int, draft_id: str) -> None:
        self.repository.soft_delete(draft_id, user_id)

    @staticmethod
    def extract_explicit_scene(record: CreationDraftRecord) -> str | None:
        digital = record.digital_human_params or {}
        content_info = record.content_info or {}
        raw_scene = str(digital.get("video_purpose") or content_info.get("purpose_scene") or "").strip()
        if not raw_scene:
            return None
        return raw_scene if raw_scene in SCENE_NAME_TO_CODE else None

    @classmethod
    def resolve_scene_code(cls, record: CreationDraftRecord) -> str:
        explicit_scene = cls.extract_explicit_scene(record)
        if explicit_scene:
            return SCENE_NAME_TO_CODE[explicit_scene]
        return cls._infer_scene_code(record)

    @staticmethod
    def _infer_scene_code(record: CreationDraftRecord) -> str:
        digital = record.digital_human_params or {}
        content_info = record.content_info or {}
        clip_params = record.clip_params or {}
        voice_params = record.voice_params or {}

        model_scene = digital.get("model_scene") if isinstance(digital.get("model_scene"), dict) else {}
        has_model_signals = bool(
            model_scene
            or digital.get("template") == "模特数字人"
            or str(digital.get("scene") or "").strip() == "模特场景"
            or str(record.status or "").strip().lower() == "gallery_generated"
        )
        has_clip_signals = bool(
            clip_params.get("render_plan")
            or clip_params.get("playback_path")
            or clip_params.get("output_url")
            or content_info.get("selected_product_id")
        )
        has_talk_signals = bool(
            record.transcript
            or record.extracted_copy
            or record.rewritten_copy
            or voice_params.get("audio_url")
            or voice_params.get("local_audio_url")
            or voice_params.get("source_audio_url")
            or str(clip_params.get("template_mode") or "").strip().lower() == "talking_head"
        )

        if has_model_signals:
            return "model"
        if has_clip_signals:
            return "clip"
        if has_talk_signals:
            return "talk"
        return "talk"

    @staticmethod
    def resolve_current_step_code(status: str | None) -> str | None:
        status_value = (status or "").strip().lower()
        if status_value in {"draft", "extracted"}:
            return "copywriting"
        if status_value in {"rewritten"}:
            return "rewrite"
        if "voice" in status_value:
            return "voice"
        if "video" in status_value:
            return "digital_human"
        if status_value in {"completed", "gallery_generated"}:
            return "completed"
        return None

    @staticmethod
    def resolve_progress(status: str | None) -> int | None:
        status_value = (status or "").strip().lower()
        if status_value == "draft":
            return 10
        if status_value == "extracted":
            return 25
        if status_value == "rewritten":
            return 45
        if "voice" in status_value:
            return 60
        if "video" in status_value:
            return 80
        if status_value in {"completed", "gallery_generated"}:
            return 100
        return None

    @staticmethod
    def _to_read(record: AvatarDraftRecord) -> AvatarDraftRead:
        return AvatarDraftRead(
            draft_id=record.draft_id,
            user_id=record.user_id,
            scene_code=record.scene_code,
            title=record.title,
            status=record.status,
            current_step_code=record.current_step_code,
            progress=record.progress,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
