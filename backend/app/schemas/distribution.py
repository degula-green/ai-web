from __future__ import annotations

import builtins
from typing import Any, List, Literal

from pydantic import BaseModel, Field


class DistributionRequest(BaseModel):
    task_id: str
    platform: str = "douyin"


class DistributionResult(BaseModel):
    task_id: str
    platform: str
    status: str


class DistributionPublishRequest(BaseModel):
    draft_id: str | None = Field(default=None, max_length=64)
    task_ref: str | None = Field(default=None, max_length=255)
    video_url: str | None = Field(default=None, max_length=2048)
    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    topics: List[str] = Field(default_factory=list)
    brand_id: str | None = Field(default=None, max_length=64)
    brand_name: str | None = Field(default=None, max_length=255)
    product_name: str | None = Field(default=None, max_length=255)
    product_link: str | None = Field(default=None, max_length=2048)
    publish_time_type: Literal["now", "schedule"] = "now"
    scheduled_at: str | None = Field(default=None, max_length=64)
    publish_mode: Literal["headed", "headless"] = "headless"
    selected_accounts: List["DistributionSelectedAccount"] = Field(default_factory=list)


class DistributionSelectedAccount(BaseModel):
    platform_type: int
    account_id: int


class DistributionPlatformResult(BaseModel):
    platform_type: int
    platform_name: str
    account_id: int
    status: str
    downstream_status_code: int
    downstream_message: str
    downstream_payload: dict[str, Any] | None = None


class DistributionPublishResult(BaseModel):
    title: str
    video_url: str
    draft_id: str | None = None
    task_ref: str | None = None
    publish_time_type: Literal["now", "schedule"]
    scheduled_at: str | None = None
    publish_mode: Literal["headed", "headless"]
    topics: List[str] = Field(default_factory=list)
    results: List[DistributionPlatformResult] = Field(default_factory=list)


class PublishPlanSummary(BaseModel):
    total_count: int = 0
    pending_count: int = 0
    success_count: int = 0
    failed_count: int = 0


class PublishPlanCalendarItem(BaseModel):
    id: int
    request_group_id: str
    date: str
    datetime: str | None = None
    platform_type: int
    platform_code: str
    platform_name: str
    account_id: int
    account_name: str
    title: str
    cover_url: str | None = None
    status: str
    publish_time_type: str
    scheduled_at: str | None = None
    submitted_at: str | None = None


class PublishPlanPendingItem(BaseModel):
    id: int
    request_group_id: str
    platform_type: int
    platform_code: str
    platform_name: str
    account_id: int
    account_name: str
    title: str
    cover_url: str | None = None
    status: str
    status_message: str | None = None
    publish_time_type: str
    scheduled_at: str | None = None
    submitted_at: str | None = None


class PublishPlanOverviewResponse(BaseModel):
    month: str
    summary: PublishPlanSummary
    calendar_items: List[PublishPlanCalendarItem] = Field(default_factory=list)
    pending_items: List[PublishPlanPendingItem] = Field(default_factory=list)


class DistributionContentItem(BaseModel):
    relation_id: int | None = None
    account_id: int | None = None
    account_name: str | None = None
    account_avatar_url: str | None = None
    platform_code: str
    platform_name: str
    content_id: str
    title: str
    description: str | None = None
    content_kind: str = "video"
    cover_url: str | None = None
    content_url: str | None = None
    author_name: str | None = None
    status: str = "synced"
    status_label: str = "已同步"
    published_at: str | None = None
    view_count: int = 0
    liked_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    collected_at: str | None = None


class DistributionContentListResponse(BaseModel):
    list: List[DistributionContentItem] = Field(default_factory=list)
    total: int = 0
    platform_options: List[str] = Field(default_factory=builtins.list)
