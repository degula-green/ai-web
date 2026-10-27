from __future__ import annotations

import re
from pathlib import Path

from app.adapters.storage.base import BaseObjectStorage
from app.schemas.upload import AssetUploadTicketRead, AssetUploadTicketRequest
from app.utils.ids import generate_id


class UploadService:
    def __init__(self, *, storage: BaseObjectStorage) -> None:
        self.storage = storage

    def create_ticket(self, payload: AssetUploadTicketRequest) -> AssetUploadTicketRead:
        module = self._normalize_segment(payload.module)
        media_type = self._normalize_media_type(payload.media_type)
        original_name = Path(payload.file_name).name
        extension = Path(original_name).suffix.lower()
        if not extension:
            extension = self._guess_extension(payload.content_type)

        object_name = "/".join(filter(None, [
            "creation-assets",
            module,
            media_type,
            payload.draft_id or "",
            f"{generate_id('asset')}{extension}",
        ]))
        upload_url, file_url = self.storage.generate_presigned_upload(
            object_name,
            content_type=payload.content_type,
        )
        return AssetUploadTicketRead(
            module=module,
            media_type=media_type,
            object_name=object_name,
            upload_url=upload_url,
            file_url=file_url,
            content_type=payload.content_type,
        )

    @staticmethod
    def _normalize_segment(value: str) -> str:
        sanitized = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-").lower()
        return sanitized or "misc"

    @classmethod
    def _normalize_media_type(cls, value: str) -> str:
        normalized = cls._normalize_segment(value)
        if normalized not in {"audio", "image", "video"}:
            return "file"
        return normalized

    @staticmethod
    def _guess_extension(content_type: str) -> str:
        mapping = {
            "audio/mpeg": ".mp3",
            "audio/wav": ".wav",
            "audio/x-wav": ".wav",
            "audio/mp4": ".m4a",
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "video/mp4": ".mp4",
            "video/quicktime": ".mov",
        }
        return mapping.get(content_type.lower(), "")
