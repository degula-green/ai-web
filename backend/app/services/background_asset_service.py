from __future__ import annotations

from pathlib import Path

from app.core.exceptions import ContractError
from app.db.repositories.background_asset_repository import BackgroundAssetRecord, BackgroundAssetRepository
from app.schemas.background_asset import (
    BackgroundAssetCreateRequest,
    BackgroundAssetListResponse,
    BackgroundAssetRead,
)


class BackgroundAssetService:
    def __init__(self, *, repository: BackgroundAssetRepository) -> None:
        self.repository = repository

    def initialize(self) -> None:
        self.repository.ensure_table()

    def list_available(self, *, user_id: int, media_type: str | None = None) -> BackgroundAssetListResponse:
        normalized_media_type = self._normalize_media_type(media_type) if media_type else None
        records = self.repository.list_available(user_id=user_id, media_type=normalized_media_type)
        return BackgroundAssetListResponse(items=[self._to_read(item) for item in records])

    def create_user_asset(self, *, user_id: int, payload: BackgroundAssetCreateRequest) -> BackgroundAssetRead:
        record = self.repository.create_user_asset(
            user_id=user_id,
            name=payload.name.strip() or Path(payload.asset_url).name or "未命名背景",
            media_type=self._normalize_media_type(payload.media_type),
            asset_url=payload.asset_url.strip(),
            thumbnail_url=(payload.thumbnail_url or "").strip() or None,
        )
        return self._to_read(record)

    def delete_user_asset(self, *, user_id: int, asset_id: int) -> None:
        if not self.repository.soft_delete_user_asset(user_id=user_id, asset_id=asset_id):
            raise ContractError("背景素材不存在或无权限删除", status_code=404)

    @staticmethod
    def _normalize_media_type(media_type: str) -> str:
        normalized = media_type.strip().lower()
        if normalized not in {"image", "video"}:
            raise ContractError("背景素材类型仅支持 image 或 video", status_code=400)
        return normalized

    @staticmethod
    def _to_read(record: BackgroundAssetRecord) -> BackgroundAssetRead:
        return BackgroundAssetRead(
            id=record.id,
            user_id=record.user_id,
            name=record.name,
            media_type=record.media_type,
            asset_url=record.asset_url,
            thumbnail_url=record.thumbnail_url,
            source_type=record.source_type,
            status=record.status,
            sort_order=record.sort_order,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
