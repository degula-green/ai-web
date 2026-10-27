from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Any

from sqlalchemy import Select, desc, func, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.publish_plan import PublishPlanItemModel


@dataclass(slots=True)
class PublishPlanItemRecord:
    id: int | None = None
    request_group_id: str = ""
    owner_user_id: int = 0
    draft_id: str | None = None
    task_ref: str | None = None
    platform_type: int = 0
    platform_code: str = ""
    platform_name: str = ""
    account_id: int = 0
    account_name: str = ""
    title: str = ""
    video_url: str | None = None
    cover_url: str | None = None
    topics: list[str] = field(default_factory=list)
    publish_mode: str = "headless"
    publish_time_type: str = "now"
    scheduled_at: str | None = None
    submitted_at: str | None = None
    status: str = "submitted"
    status_message: str | None = None
    downstream_status_code: int | None = None
    downstream_payload: dict[str, Any] | None = None
    downstream_response: dict[str, Any] | None = None
    extra_data: dict[str, Any] | None = None
    failure_reason: str | None = None
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_model(cls, model: PublishPlanItemModel) -> "PublishPlanItemRecord":
        return cls(
            id=int(model.id),
            request_group_id=model.request_group_id,
            owner_user_id=int(model.owner_user_id),
            draft_id=model.draft_id,
            task_ref=model.task_ref,
            platform_type=int(model.platform_type),
            platform_code=model.platform_code,
            platform_name=model.platform_name,
            account_id=int(model.account_id),
            account_name=model.account_name,
            title=model.title,
            video_url=model.video_url,
            cover_url=model.cover_url,
            topics=list(model.topics or []),
            publish_mode=model.publish_mode,
            publish_time_type=model.publish_time_type,
            scheduled_at=model.scheduled_at.isoformat() if model.scheduled_at else None,
            submitted_at=model.submitted_at.isoformat() if model.submitted_at else None,
            status=model.status,
            status_message=model.status_message,
            downstream_status_code=model.downstream_status_code,
            downstream_payload=model.downstream_payload or None,
            downstream_response=model.downstream_response or None,
            extra_data=model.extra_data or None,
            failure_reason=model.failure_reason,
            created_at=model.created_at.isoformat() if model.created_at else "",
            updated_at=model.updated_at.isoformat() if model.updated_at else "",
        )


class PublishPlanRepository:
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
        CREATE TABLE IF NOT EXISTS publish_plan_items (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            request_group_id VARCHAR(64) NOT NULL,
            owner_user_id BIGINT NOT NULL,
            draft_id VARCHAR(64) NULL,
            task_ref VARCHAR(255) NULL,
            platform_type INT NOT NULL,
            platform_code VARCHAR(32) NOT NULL,
            platform_name VARCHAR(64) NOT NULL,
            account_id BIGINT NOT NULL,
            account_name VARCHAR(255) NOT NULL,
            title VARCHAR(255) NOT NULL,
            video_url VARCHAR(2048) NULL,
            cover_url VARCHAR(1024) NULL,
            topics JSON NOT NULL,
            publish_mode VARCHAR(32) NOT NULL,
            publish_time_type VARCHAR(32) NOT NULL,
            scheduled_at DATETIME NULL,
            submitted_at DATETIME NULL,
            status VARCHAR(32) NOT NULL,
            status_message VARCHAR(512) NULL,
            downstream_status_code INT NULL,
            downstream_payload JSON NULL,
            downstream_response JSON NULL,
            extra_data JSON NULL,
            failure_reason TEXT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            KEY idx_publish_plan_items_owner_user_id (owner_user_id),
            KEY idx_publish_plan_items_request_group_id (request_group_id),
            KEY idx_publish_plan_items_draft_id (draft_id),
            KEY idx_publish_plan_items_task_ref (task_ref),
            KEY idx_publish_plan_items_platform_type (platform_type),
            KEY idx_publish_plan_items_platform_code (platform_code),
            KEY idx_publish_plan_items_account_id (account_id),
            KEY idx_publish_plan_items_publish_time_type (publish_time_type),
            KEY idx_publish_plan_items_scheduled_at (scheduled_at),
            KEY idx_publish_plan_items_submitted_at (submitted_at),
            KEY idx_publish_plan_items_status (status),
            KEY idx_publish_plan_items_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        with self.session_scope() as session:
            session.execute(text(ddl))

    def create_item(self, record: PublishPlanItemRecord) -> PublishPlanItemRecord:
        with self.session_scope() as session:
            model = PublishPlanItemModel(
                request_group_id=record.request_group_id,
                owner_user_id=record.owner_user_id,
                draft_id=record.draft_id,
                task_ref=record.task_ref,
                platform_type=record.platform_type,
                platform_code=record.platform_code,
                platform_name=record.platform_name,
                account_id=record.account_id,
                account_name=record.account_name,
                title=record.title,
                video_url=record.video_url,
                cover_url=record.cover_url,
                topics=record.topics,
                publish_mode=record.publish_mode,
                publish_time_type=record.publish_time_type,
                scheduled_at=self._parse_datetime(record.scheduled_at),
                submitted_at=self._parse_datetime(record.submitted_at),
                status=record.status,
                status_message=record.status_message,
                downstream_status_code=record.downstream_status_code,
                downstream_payload=self._normalize_json_value(record.downstream_payload),
                downstream_response=self._normalize_json_value(record.downstream_response),
                extra_data=self._normalize_json_value(record.extra_data),
                failure_reason=record.failure_reason,
            )
            session.add(model)
            session.flush()
            session.refresh(model)
            return PublishPlanItemRecord.from_model(model)

    def list_calendar_items(
        self,
        *,
        user_id: int,
        start_at: datetime,
        end_at: datetime,
    ) -> list[PublishPlanItemRecord]:
        with self.session_scope() as session:
            display_time = func.coalesce(PublishPlanItemModel.scheduled_at, PublishPlanItemModel.submitted_at, PublishPlanItemModel.created_at)
            stmt: Select[tuple[PublishPlanItemModel]] = (
                select(PublishPlanItemModel)
                .where(
                    PublishPlanItemModel.owner_user_id == user_id,
                    display_time >= start_at,
                    display_time < end_at,
                    PublishPlanItemModel.status.in_(["submitted", "scheduled"]),
                )
                .order_by(desc(display_time), desc(PublishPlanItemModel.id))
            )
            return [PublishPlanItemRecord.from_model(item) for item in session.scalars(stmt).all()]

    def list_pending_items(self, *, user_id: int, now: datetime, limit: int = 20) -> list[PublishPlanItemRecord]:
        with self.session_scope() as session:
            stmt: Select[tuple[PublishPlanItemModel]] = (
                select(PublishPlanItemModel)
                .where(
                    PublishPlanItemModel.owner_user_id == user_id,
                    PublishPlanItemModel.publish_time_type == "schedule",
                    PublishPlanItemModel.scheduled_at.is_not(None),
                    PublishPlanItemModel.scheduled_at >= now,
                    PublishPlanItemModel.status.in_(["scheduled", "submitted"]),
                )
                .order_by(PublishPlanItemModel.scheduled_at.asc(), PublishPlanItemModel.id.desc())
                .limit(limit)
            )
            return [PublishPlanItemRecord.from_model(item) for item in session.scalars(stmt).all()]

    def summary(self, *, user_id: int, now: datetime) -> dict[str, int]:
        with self.session_scope() as session:
            base_filters = [PublishPlanItemModel.owner_user_id == user_id]
            total_count = session.scalar(select(func.count()).select_from(PublishPlanItemModel).where(*base_filters)) or 0
            pending_count = (
                session.scalar(
                    select(func.count()).select_from(PublishPlanItemModel).where(
                        *base_filters,
                        PublishPlanItemModel.publish_time_type == "schedule",
                        PublishPlanItemModel.scheduled_at.is_not(None),
                        PublishPlanItemModel.scheduled_at >= now,
                        PublishPlanItemModel.status.in_(["scheduled", "submitted"]),
                    )
                )
                or 0
            )
            success_count = (
                session.scalar(
                    select(func.count()).select_from(PublishPlanItemModel).where(
                        *base_filters,
                        PublishPlanItemModel.status.in_(["submitted", "scheduled"]),
                    )
                )
                or 0
            )
            failed_count = (
                session.scalar(
                    select(func.count()).select_from(PublishPlanItemModel).where(
                        *base_filters,
                        PublishPlanItemModel.status == "failed",
                    )
                )
                or 0
            )
            return {
                "total_count": int(total_count),
                "pending_count": int(pending_count),
                "success_count": int(success_count),
                "failed_count": int(failed_count),
            }

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        return datetime.fromisoformat(value)

    @classmethod
    def _normalize_json_value(cls, value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, (datetime, date, time)):
            return value.isoformat()
        if isinstance(value, dict):
            return {str(key): cls._normalize_json_value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [cls._normalize_json_value(item) for item in value]
        return str(value)
