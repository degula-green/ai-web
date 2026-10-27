from __future__ import annotations

from datetime import datetime

from app.db.repositories.publish_plan_repository import PublishPlanItemRecord, PublishPlanRepository
from app.schemas.distribution import (
    PublishPlanCalendarItem,
    PublishPlanOverviewResponse,
    PublishPlanPendingItem,
    PublishPlanSummary,
)


class PublishPlanService:
    def __init__(self, *, repository: PublishPlanRepository) -> None:
        self.repository = repository

    def initialize(self) -> None:
        self.repository.ensure_table()

    def get_overview(self, *, user_id: int, month: str | None = None) -> PublishPlanOverviewResponse:
        month_start = self._resolve_month_start(month)
        if month_start.month == 12:
            next_month_start = datetime(month_start.year + 1, 1, 1)
        else:
            next_month_start = datetime(month_start.year, month_start.month + 1, 1)

        calendar_records = self.repository.list_calendar_items(
            user_id=user_id,
            start_at=month_start,
            end_at=next_month_start,
        )
        now = datetime.now()
        pending_records = self.repository.list_pending_items(user_id=user_id, now=now, limit=20)
        summary = self.repository.summary(user_id=user_id, now=now)
        return PublishPlanOverviewResponse(
            month=month_start.strftime("%Y-%m"),
            summary=PublishPlanSummary(**summary),
            calendar_items=[self._to_calendar_item(item) for item in calendar_records],
            pending_items=[self._to_pending_item(item) for item in pending_records],
        )

    @staticmethod
    def _resolve_month_start(month: str | None) -> datetime:
        if month:
            return datetime.strptime(f"{month}-01", "%Y-%m-%d")
        now = datetime.now()
        return datetime(now.year, now.month, 1)

    @staticmethod
    def _to_calendar_item(record: PublishPlanItemRecord) -> PublishPlanCalendarItem:
        display_at = record.scheduled_at or record.submitted_at or record.created_at
        return PublishPlanCalendarItem(
            id=record.id or 0,
            request_group_id=record.request_group_id,
            date=(display_at or "")[:10],
            datetime=display_at,
            platform_type=record.platform_type,
            platform_code=record.platform_code,
            platform_name=record.platform_name,
            account_id=record.account_id,
            account_name=record.account_name,
            title=record.title,
            cover_url=record.cover_url,
            status=record.status,
            publish_time_type=record.publish_time_type,
            scheduled_at=record.scheduled_at,
            submitted_at=record.submitted_at,
        )

    @staticmethod
    def _to_pending_item(record: PublishPlanItemRecord) -> PublishPlanPendingItem:
        return PublishPlanPendingItem(
            id=record.id or 0,
            request_group_id=record.request_group_id,
            platform_type=record.platform_type,
            platform_code=record.platform_code,
            platform_name=record.platform_name,
            account_id=record.account_id,
            account_name=record.account_name,
            title=record.title,
            cover_url=record.cover_url,
            status=record.status,
            status_message=record.status_message,
            publish_time_type=record.publish_time_type,
            scheduled_at=record.scheduled_at,
            submitted_at=record.submitted_at,
        )
