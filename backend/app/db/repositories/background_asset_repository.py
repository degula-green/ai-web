from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy import Select, asc, desc, or_, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.background_asset import BackgroundAssetModel


@dataclass(slots=True)
class BackgroundAssetRecord:
    id: int
    user_id: int | None
    name: str
    media_type: str
    asset_url: str
    thumbnail_url: str | None
    source_type: str
    status: str
    sort_order: int
    created_at: str
    updated_at: str

    @classmethod
    def from_model(cls, model: BackgroundAssetModel) -> "BackgroundAssetRecord":
        return cls(
            id=int(model.id),
            user_id=model.user_id,
            name=model.name,
            media_type=model.media_type,
            asset_url=model.asset_url,
            thumbnail_url=model.thumbnail_url,
            source_type=model.source_type,
            status=model.status,
            sort_order=int(model.sort_order or 0),
            created_at=model.created_at.isoformat() if model.created_at else "",
            updated_at=model.updated_at.isoformat() if model.updated_at else "",
        )


class BackgroundAssetRepository:
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
        CREATE TABLE IF NOT EXISTS background_assets (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT NULL,
            name VARCHAR(128) NOT NULL,
            media_type VARCHAR(16) NOT NULL,
            asset_url VARCHAR(1024) NOT NULL,
            thumbnail_url VARCHAR(1024) NULL,
            source_type VARCHAR(16) NOT NULL DEFAULT 'user',
            status VARCHAR(16) NOT NULL DEFAULT 'active',
            sort_order INT NOT NULL DEFAULT 0,
            is_deleted TINYINT NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            KEY idx_background_assets_user_id (user_id),
            KEY idx_background_assets_media_type (media_type),
            KEY idx_background_assets_source_type (source_type),
            KEY idx_background_assets_status (status),
            KEY idx_background_assets_is_deleted (is_deleted)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        with self.session_scope() as session:
            session.execute(text(ddl))

    def list_available(self, *, user_id: int, media_type: str | None = None) -> list[BackgroundAssetRecord]:
        with self.session_scope() as session:
            stmt: Select[tuple[BackgroundAssetModel]] = select(BackgroundAssetModel).where(
                BackgroundAssetModel.is_deleted == 0,
                BackgroundAssetModel.status == "active",
                or_(BackgroundAssetModel.source_type == "official", BackgroundAssetModel.user_id == user_id),
            )
            if media_type:
                stmt = stmt.where(BackgroundAssetModel.media_type == media_type)

            stmt = stmt.order_by(
                asc(BackgroundAssetModel.source_type),
                desc(BackgroundAssetModel.sort_order),
                desc(BackgroundAssetModel.updated_at),
                desc(BackgroundAssetModel.id),
            )
            return [BackgroundAssetRecord.from_model(item) for item in session.scalars(stmt).all()]

    def create_user_asset(
        self,
        *,
        user_id: int,
        name: str,
        media_type: str,
        asset_url: str,
        thumbnail_url: str | None,
    ) -> BackgroundAssetRecord:
        with self.session_scope() as session:
            model = BackgroundAssetModel(
                user_id=user_id,
                name=name,
                media_type=media_type,
                asset_url=asset_url,
                thumbnail_url=thumbnail_url,
                source_type="user",
                status="active",
            )
            session.add(model)
            session.flush()
            session.refresh(model)
            return BackgroundAssetRecord.from_model(model)

    def soft_delete_user_asset(self, *, user_id: int, asset_id: int) -> bool:
        with self.session_scope() as session:
            model = session.scalar(
                select(BackgroundAssetModel).where(
                    BackgroundAssetModel.id == asset_id,
                    BackgroundAssetModel.user_id == user_id,
                    BackgroundAssetModel.source_type == "user",
                    BackgroundAssetModel.is_deleted == 0,
                )
            )
            if model is None:
                return False
            model.is_deleted = 1
            return True
