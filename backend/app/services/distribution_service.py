from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from app.adapters.channel.base import BaseChannelPlugin
from app.core.exceptions import ContractError
from app.db.models.platform_account import PlatformAccount, PlatformAccountSession
from app.db.repositories.content_repository import ContentRepository
from app.db.repositories.creation_draft_repository import CreationDraftRepository
from app.db.repositories.platform_account_content_repository import PlatformAccountContentRepository
from app.db.repositories.publish_plan_repository import PublishPlanItemRecord, PublishPlanRepository
from app.modules.publishing.infrastructure.runtime.social_auto_upload_runtime import (
    SocialAccountState,
    SocialAutoUploadRuntime,
)
from app.schemas.distribution import (
    DistributionPlatformResult,
    DistributionPublishRequest,
    DistributionPublishResult,
    DistributionRequest,
    DistributionResult,
)
from app.utils.hashing import sha256_text
from app.utils.ids import generate_id


class DistributionService:
    STATUS_MESSAGE_LIMIT = 500

    def __init__(
        self,
        *,
        channel_plugin: BaseChannelPlugin,
        session_factory: sessionmaker[Session],
        content_repository: ContentRepository,
        platform_account_content_repository: PlatformAccountContentRepository,
        creation_draft_repository: CreationDraftRepository,
        publish_plan_repository: PublishPlanRepository,
        publisher_runtime: SocialAutoUploadRuntime,
    ) -> None:
        self.channel_plugin = channel_plugin
        self.session_factory = session_factory
        self.content_repository = content_repository
        self.platform_account_content_repository = platform_account_content_repository
        self.creation_draft_repository = creation_draft_repository
        self.publish_plan_repository = publish_plan_repository
        self.publisher_runtime = publisher_runtime

    def dispatch(self, payload: DistributionRequest) -> DistributionResult:
        self.channel_plugin.send_alert(f"Distribution task received for {payload.task_id}")
        return DistributionResult(task_id=payload.task_id, platform=payload.platform, status="queued_stub")

    async def list_content_items(
        self,
        *,
        user_id: int,
        platform_code: str | None = None,
        content_status: str | None = None,
        keyword: str | None = None,
    ) -> dict[str, Any]:
        normalized_platform = self._normalize_content_platform(platform_code)
        status_filter = self._normalize_content_status(content_status)
        rows = self.platform_account_content_repository.list_items(
            owner_user_id=user_id,
            platform_code=normalized_platform or None,
            content_status=status_filter or None,
            keyword=keyword,
        )
        if not status_filter:
            rows = [row for row in rows if str(getattr(row, "content_status", "") or "").strip().lower() != "deleted"]

        account_map = self._load_account_meta_map(
            user_id=user_id,
            account_ids=[
                self._safe_int(getattr(row, "account_id", None))
                for row in rows
                if self._safe_int(getattr(row, "account_id", None)) > 0
            ],
        )
        items = [self._build_distribution_content_item_v2(row, account_map=account_map) for row in rows]

        return {
            "list": items,
            "total": len(items),
            "platform_options": ["all", "douyin", "xiaohongshu", "bilibili", "kuaishou"],
        }

    def publish_for_user(self, *, user_id: int, payload: DistributionPublishRequest) -> DistributionPublishResult:
        if not payload.selected_accounts:
            raise ContractError("请至少选择一个发布账号", status_code=400)

        draft_id = self._resolve_draft_id(payload)
        draft = self.creation_draft_repository.get(draft_id, user_id) if draft_id else None

        raw_title = (payload.title or "").strip() or (draft.title.strip() if draft and draft.title else "")
        if not raw_title:
            raise ContractError("发布标题不能为空", status_code=400)
        raw_description = (payload.description or "").strip() or self._resolve_draft_description(draft) or raw_title

        video_url = (payload.video_url or "").strip() or self._resolve_draft_video_url(draft)
        if not video_url:
            raise ContractError("缺少可发布的视频地址", status_code=400)

        topics = self._normalize_topics(payload.topics or self._resolve_draft_topics(draft))
        schedule_config = self._build_schedule_config(payload.publish_time_type, payload.scheduled_at)
        selected_accounts = self._resolve_selected_accounts(user_id=user_id, raw_accounts=payload.selected_accounts)
        request_group_id = generate_id("pubplan")
        task_ref = (payload.task_ref or "").strip() or draft_id
        cover_url = self._resolve_draft_cover_url(draft)
        thumbnail_path = self._resolve_publish_thumbnail_path(cover_url)
        headless = payload.publish_mode != "headed"
        publish_extra_data = self._build_publish_extra_data(
            description=raw_description,
            brand_id=payload.brand_id,
            brand_name=payload.brand_name,
            product_name=payload.product_name,
            product_link=payload.product_link,
        )

        results: list[DistributionPlatformResult] = []
        for item in selected_accounts:
            platform_content = self._build_platform_publish_content(
                platform_code=str(item["platform_code"]),
                raw_title=raw_title,
                raw_description=raw_description,
                topics=topics,
            )
            platform_title = str(platform_content["title"])
            platform_description = str(platform_content["description"])
            platform_topics = list(platform_content["topics"])
            runtime_payload = {
                "type": int(item["platform_type"]),
                "title": platform_title,
                "desc": platform_description,
                "tags": platform_topics,
                "fileList": [video_url],
                "accountIds": [int(item["account_id"])],
                "headless": headless,
                "publishMode": payload.publish_mode,
                "productLink": str(payload.product_link or "").strip(),
                "productTitle": str(payload.product_name or "").strip(),
                **schedule_config,
            }

            try:
                runtime_response = self.publisher_runtime.publish(
                    platform_type=int(item["platform_type"]),
                    title=platform_title,
                    description=platform_description,
                    file_list=[video_url],
                    accounts=[
                        SocialAccountState(
                            account_id=int(item["account_id"]),
                            platform_type=int(item["platform_type"]),
                            platform_code=str(item["platform_code"]),
                            platform_name=str(item["platform_name"]),
                            account_name=str(item["account_name"]),
                            cookies=list(item["cookies"]),
                            local_storage=item["local_storage"],
                        )
                    ],
                    tags=platform_topics,
                    category=None,
                    enable_timer=bool(schedule_config.get("enableTimer")),
                    videos_per_day=int(schedule_config.get("videosPerDay") or 1),
                    daily_times=schedule_config.get("dailyTimes"),
                    start_days=int(schedule_config.get("startDays") or 0),
                    publish_datetime=schedule_config.get("publishDatetime"),
                    thumbnail_path=thumbnail_path,
                    product_link=str(payload.product_link or "").strip(),
                    product_title=str(payload.product_name or "").strip(),
                    headless=headless,
                )
                self._sync_runtime_session_state(
                    account_id=int(item["account_id"]),
                    platform_code=str(item["platform_code"]),
                )
            except ContractError as exc:
                failure_message = str(exc)
                self.publish_plan_repository.create_item(
                    self._build_publish_plan_record(
                        request_group_id=request_group_id,
                        user_id=user_id,
                        draft_id=draft_id,
                        task_ref=task_ref,
                        title=platform_title,
                        video_url=video_url,
                        cover_url=cover_url,
                        topics=platform_topics,
                        publish_mode=payload.publish_mode,
                        publish_time_type=payload.publish_time_type,
                        scheduled_at=payload.scheduled_at,
                        account_item=item,
                        status="failed",
                        status_message=self._summarize_status_message(failure_message),
                        downstream_payload=runtime_payload,
                        downstream_response=None,
                        downstream_status_code=getattr(exc, "status_code", None),
                        extra_data=publish_extra_data,
                        failure_reason=failure_message,
                    )
                )
                raise

            status = "scheduled" if payload.publish_time_type == "schedule" else "submitted"
            self.publish_plan_repository.create_item(
                self._build_publish_plan_record(
                    request_group_id=request_group_id,
                    user_id=user_id,
                    draft_id=draft_id,
                    task_ref=task_ref,
                    title=platform_title,
                    video_url=video_url,
                    cover_url=cover_url,
                    topics=platform_topics,
                    publish_mode=payload.publish_mode,
                    publish_time_type=payload.publish_time_type,
                    scheduled_at=payload.scheduled_at,
                    account_item=item,
                    status=status,
                    status_message=self._summarize_status_message(str(runtime_response["message"])),
                    downstream_payload=runtime_payload,
                    downstream_response=runtime_response.get("data"),
                    downstream_status_code=int(runtime_response["status_code"]),
                    extra_data=publish_extra_data,
                    failure_reason=None,
                )
            )
            results.append(
                DistributionPlatformResult(
                    platform_type=int(item["platform_type"]),
                    platform_name=str(item["platform_name"]),
                    account_id=int(item["account_id"]),
                    status=status,
                    downstream_status_code=int(runtime_response["status_code"]),
                    downstream_message=str(runtime_response["message"]),
                    downstream_payload=runtime_payload,
                )
            )

        return DistributionPublishResult(
            title=self._clean_publish_title(raw_title),
            video_url=video_url,
            draft_id=draft_id,
            task_ref=task_ref,
            publish_time_type=payload.publish_time_type,
            scheduled_at=payload.scheduled_at,
            publish_mode=payload.publish_mode,
            topics=topics,
            results=results,
        )

    @staticmethod
    def _resolve_draft_id(payload: DistributionPublishRequest) -> str | None:
        if payload.draft_id:
            return payload.draft_id.strip()
        if payload.task_ref and payload.task_ref.strip().startswith("draft_"):
            return payload.task_ref.strip()
        return None

    @staticmethod
    def _resolve_draft_video_url(draft: Any) -> str:
        if draft is None:
            return ""
        digital = draft.digital_human_params if isinstance(draft.digital_human_params, dict) else {}
        clip = draft.clip_params if isinstance(draft.clip_params, dict) else {}
        content_info = draft.content_info if isinstance(draft.content_info, dict) else {}
        candidates = (
            clip.get("output_url"),
            clip.get("merged_output_url"),
            clip.get("clipped_video_playback_path"),
            clip.get("clipped_video_url"),
            content_info.get("local_video_url"),
            digital.get("local_video_url"),
            digital.get("generated_video_url"),
            digital.get("video_url"),
            digital.get("generated_video_source_url"),
            content_info.get("video_url"),
        )
        for item in candidates:
            value = str(item or "").strip()
            if value:
                return value
        return ""

    @staticmethod
    def _resolve_draft_cover_url(draft: Any) -> str | None:
        if draft is None:
            return None
        content_info = draft.content_info if isinstance(draft.content_info, dict) else {}
        digital = draft.digital_human_params if isinstance(draft.digital_human_params, dict) else {}
        candidates = (
            content_info.get("cover_url"),
            content_info.get("thumbnail_url"),
            content_info.get("thumbnail"),
            content_info.get("cover"),
            digital.get("cover_url"),
        )
        for item in candidates:
            value = str(item or "").strip()
            if value:
                return value
        return None

    @staticmethod
    def _resolve_draft_description(draft: Any) -> str:
        if draft is None:
            return ""
        candidates = (
            getattr(draft, "rewritten_copy", None),
            getattr(draft, "extracted_copy", None),
            getattr(draft, "title", None),
        )
        for item in candidates:
            value = str(item or "").strip()
            if value:
                return value
        content_info = draft.content_info if isinstance(draft.content_info, dict) else {}
        extra_candidates = (
            content_info.get("description"),
            content_info.get("desc"),
            content_info.get("content"),
        )
        for item in extra_candidates:
            value = str(item or "").strip()
            if value:
                return value
        return ""

    @staticmethod
    def _resolve_publish_thumbnail_path(raw_value: str | None) -> str:
        value = str(raw_value or "").strip()
        if not value:
            return ""
        if re.match(r"^https?://", value, re.IGNORECASE):
            return ""
        path = Path(value)
        if path.is_file():
            return str(path.resolve())
        return ""

    @classmethod
    def _resolve_draft_topics(cls, draft: Any) -> list[str]:
        if draft is None:
            return []
        content_info = draft.content_info if isinstance(draft.content_info, dict) else {}
        raw_tags = content_info.get("tags")
        if isinstance(raw_tags, list):
            return cls._normalize_topics(raw_tags)
        return cls._normalize_topics(re.findall(r"#([^\s#]+)", str(draft.title or "")))

    @staticmethod
    def _normalize_topics(values: list[Any]) -> list[str]:
        normalized: list[str] = []
        for item in values:
            value = str(item or "").strip().replace("#", "")
            if value and value not in normalized:
                normalized.append(value)
        return normalized

    @classmethod
    def _clean_publish_title(cls, value: str | None) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        cleaned = re.sub(r"#[^\s#]+", "", text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned or text

    @classmethod
    def _build_platform_publish_content(
        cls,
        *,
        platform_code: str,
        raw_title: str,
        raw_description: str,
        topics: list[str],
    ) -> dict[str, Any]:
        normalized_platform = str(platform_code or "").strip().lower()
        clean_title = cls._clean_publish_title(raw_title)
        clean_description = str(raw_description or "").strip() or clean_title or raw_title
        normalized_topics = cls._normalize_topics(topics)

        if normalized_platform in {"kuaishou", "ks"}:
            return {
                "title": (clean_title or raw_title)[:40],
                "description": clean_description,
                "topics": normalized_topics[:3],
            }

        if normalized_platform in {"bilibili", "bili"}:
            return {
                "title": (clean_title or raw_title)[:80],
                "description": clean_description,
                "topics": normalized_topics[:10],
            }

        if normalized_platform in {"xiaohongshu", "xhs"}:
            return {
                "title": (clean_title or raw_title)[:20],
                "description": clean_description,
                "topics": normalized_topics[:10],
            }

        if normalized_platform in {"douyin", "dy"}:
            return {
                "title": (clean_title or raw_title)[:30],
                "description": clean_description,
                "topics": normalized_topics[:10],
            }

        return {
            "title": clean_title or raw_title,
            "description": clean_description,
            "topics": normalized_topics,
        }

    def _build_schedule_config(self, publish_time_type: str, scheduled_at: str | None) -> dict[str, Any]:
        if publish_time_type != "schedule":
            return {
                "enableTimer": False,
                "videosPerDay": 1,
                "dailyTimes": None,
                "startDays": 0,
                "publishDatetime": None,
            }

        if not scheduled_at:
            raise ContractError("定时发布时间不能为空", status_code=400)

        try:
            target = datetime.fromisoformat(scheduled_at)
        except ValueError as exc:
            raise ContractError("定时发布时间格式错误", status_code=400) from exc

        now = datetime.now()
        delta_days = (target.date() - now.date()).days
        if delta_days < 1:
            raise ContractError("当前发布能力仅支持从明天开始的定时发布", status_code=400)

        return {
            "enableTimer": True,
            "videosPerDay": 1,
            "dailyTimes": [int(target.hour)],
            "startDays": delta_days - 1,
            "publishDatetime": target,
        }

    def _resolve_selected_accounts(self, *, user_id: int, raw_accounts: list[Any]) -> list[dict[str, Any]]:
        account_ids = [int(item.account_id) for item in raw_accounts]
        with self.session_factory() as session:
            accounts = (
                session.query(PlatformAccount)
                .filter(
                    PlatformAccount.owner_user_id == int(user_id),
                    PlatformAccount.id.in_(account_ids),
                    PlatformAccount.is_deleted == 0,
                )
                .all()
            )
            session_rows = (
                session.query(PlatformAccountSession)
                .filter(PlatformAccountSession.account_id.in_(account_ids))
                .all()
            )

        account_map = {int(item.id): item for item in accounts}
        session_map = {int(item.account_id): item for item in session_rows}
        resolved: list[dict[str, Any]] = []
        for item in raw_accounts:
            platform_type = int(item.platform_type)
            account_id = int(item.account_id)
            account = account_map.get(account_id)
            if not account:
                raise ContractError(f"发布账号不存在或不属于当前用户: {account_id}", status_code=400)

            expected_platform = self._platform_type_to_main_platform(platform_type)
            if account.platform_code != expected_platform:
                raise ContractError(
                    f"发布平台与账号不匹配: 账号 {account_id} 属于 {account.platform_code}",
                    status_code=400,
                )

            session_row = session_map.get(account_id)
            if not session_row or not isinstance(session_row.cookies, list) or not session_row.cookies:
                raise ContractError(f"账号 {account.account_name} 缺少可用 Cookie", status_code=400)

            resolved.append(
                {
                    "platform_type": platform_type,
                    "account_id": account_id,
                    "platform_code": account.platform_code,
                    "platform_name": self._platform_display_name(platform_type),
                    "account_name": account.nickname or account.account_name,
                    "cookies": list(session_row.cookies),
                    "local_storage": session_row.local_storage if isinstance(session_row.local_storage, dict) else None,
                }
            )
        return resolved

    @staticmethod
    def _build_publish_plan_record(
        *,
        request_group_id: str,
        user_id: int,
        draft_id: str | None,
        task_ref: str | None,
        title: str,
        video_url: str,
        cover_url: str | None,
        topics: list[str],
        publish_mode: str,
        publish_time_type: str,
        scheduled_at: str | None,
        account_item: dict[str, Any],
        status: str,
        status_message: str | None,
        downstream_payload: dict[str, Any] | None,
        downstream_response: dict[str, Any] | None,
        downstream_status_code: int | None,
        extra_data: dict[str, Any] | None,
        failure_reason: str | None,
    ) -> PublishPlanItemRecord:
        return PublishPlanItemRecord(
            request_group_id=request_group_id,
            owner_user_id=user_id,
            draft_id=draft_id,
            task_ref=task_ref,
            platform_type=int(account_item["platform_type"]),
            platform_code=str(account_item["platform_code"]),
            platform_name=str(account_item["platform_name"]),
            account_id=int(account_item["account_id"]),
            account_name=str(account_item["account_name"]),
            title=title,
            video_url=video_url,
            cover_url=cover_url,
            topics=topics,
            publish_mode=publish_mode,
            publish_time_type=publish_time_type,
            scheduled_at=scheduled_at,
            submitted_at=datetime.now().isoformat(),
            status=status,
            status_message=status_message,
            downstream_status_code=downstream_status_code,
            downstream_payload=downstream_payload,
            downstream_response=downstream_response,
            extra_data=extra_data,
            failure_reason=failure_reason,
        )

    @staticmethod
    def _build_publish_extra_data(
        *,
        description: str | None,
        brand_id: str | None,
        brand_name: str | None,
        product_name: str | None,
        product_link: str | None,
    ) -> dict[str, Any] | None:
        payload = {
            "desc": str(description or "").strip(),
            "brand_id": str(brand_id or "").strip(),
            "brand_name": str(brand_name or "").strip(),
            "product_name": str(product_name or "").strip(),
            "product_link": str(product_link or "").strip(),
        }
        normalized = {key: value for key, value in payload.items() if value}
        return normalized or None

    def _sync_runtime_session_state(self, *, account_id: int, platform_code: str) -> None:
        refreshed_state = self.publisher_runtime.load_storage_state(
            account_id=account_id,
            platform_code=platform_code,
        )
        if not isinstance(refreshed_state, dict):
            return

        cookies = refreshed_state.get("cookies")
        local_storage = refreshed_state.get("localStorage")
        if not isinstance(cookies, list) or not cookies:
            return
        if local_storage is not None and not isinstance(local_storage, dict):
            local_storage = None

        now = datetime.now()
        cookie_blob = json.dumps(cookies, ensure_ascii=False, separators=(",", ":"))
        cookie_hash = self._hash_json_payload(cookies)
        storage_hash = self._hash_json_payload(local_storage)
        expires_at = self._infer_cookie_expire_at(cookies)

        with self.session_factory() as session:
            session_row = (
                session.query(PlatformAccountSession)
                .filter(PlatformAccountSession.account_id == int(account_id))
                .first()
            )
            if not session_row:
                session_row = PlatformAccountSession(account_id=int(account_id))
                session.add(session_row)

            session_row.cookies = cookies
            session_row.local_storage = local_storage
            session_row.cookie_blob = cookie_blob
            session_row.cookie_hash = cookie_hash
            session_row.storage_hash = storage_hash
            session_row.expires_at = expires_at or session_row.expires_at
            session_row.last_sync_at = now
            session_row.auth_type = session_row.auth_type or "cookie"
            session_row.source_type = session_row.source_type or "upload_runtime"
            session_row.status = "active"
            session_row.session_status = "active"
            session_row.last_validation_error = None
            session_row.last_validated_at = now
            session_row.last_refresh_at = now
            session_row.cookie_version = int(session_row.cookie_version or 0) + 1
            session.commit()

    @classmethod
    def _summarize_status_message(cls, value: str | None) -> str | None:
        text = str(value or "").strip()
        if not text:
            return None
        compact = " ".join(text.split())
        if len(compact) <= cls.STATUS_MESSAGE_LIMIT:
            return compact
        return compact[: cls.STATUS_MESSAGE_LIMIT - 3] + "..."

    @staticmethod
    def _normalize_content_platform(platform_code: str | None) -> str:
        key = str(platform_code or "").strip().lower()
        return {
            "all": "",
            "": "",
            "douyin": "douyin",
            "dy": "douyin",
            "xiaohongshu": "xiaohongshu",
            "xhs": "xiaohongshu",
            "bilibili": "bilibili",
            "bili": "bilibili",
            "kuaishou": "kuaishou",
            "ks": "kuaishou",
        }.get(key, "")

    @staticmethod
    def _normalize_content_status(status: str | None) -> str:
        key = str(status or "").strip().lower()
        return {
            "all": "",
            "": "",
            "published": "published",
            "pending": "pending",
            "deleted": "deleted",
        }.get(key, "")

    @staticmethod
    def _build_distribution_content_item(row: dict[str, Any]) -> dict[str, Any]:
        platform_code = str(getattr(row, "platform_code", "") or "").strip().lower()
        content_id = str(getattr(row, "content_id", "") or "").strip()
        title = str(getattr(row, "title", "") or content_id or "未命名内容").strip()
        view_count = DistributionService._safe_int(getattr(row, "view_count", 0))
        liked_count = DistributionService._safe_int(getattr(row, "liked_count", 0))
        comment_count = DistributionService._safe_int(getattr(row, "comment_count", 0))
        share_count = DistributionService._safe_int(getattr(row, "share_count", 0))
        published_at_raw = getattr(row, "published_at", None)
        collected_at_raw = getattr(row, "last_synced_at", None)
        content_status = str(getattr(row, "content_status", "") or "published").strip().lower()
        return {
            "relation_id": DistributionService._safe_int(getattr(row, "id", None)) or None,
            "account_id": DistributionService._safe_int(getattr(row, "account_id", None)) or None,
            "account_name": DistributionService._extract_content_account_name(row),
            "platform_code": platform_code,
            "platform_name": DistributionService._platform_content_display_name(platform_code),
            "content_id": content_id,
            "title": title,
            "description": DistributionService._extract_content_description(getattr(row, "extra_data", None)),
            "content_kind": str(getattr(row, "content_type", "") or "video"),
            "cover_url": str(getattr(row, "cover_url", "") or "").strip() or None,
            "content_url": str(getattr(row, "content_url", "") or "").strip() or None,
            "author_name": str(getattr(row, "author_name", "") or "").strip() or None,
            "status": content_status,
            "status_label": "已发布" if content_status == "published" else "待发布",
            "published_at": published_at_raw.isoformat() if published_at_raw else None,
            "view_count": view_count,
            "liked_count": liked_count,
            "comment_count": comment_count,
            "share_count": share_count,
            "collected_at": collected_at_raw.isoformat() if collected_at_raw else None,
        }

    @staticmethod
    def _extract_content_description(extra_data: Any) -> str | None:
        if isinstance(extra_data, dict):
            value = str(extra_data.get("desc") or "").strip()
            return value or None
        return None

    @staticmethod
    def _extract_content_account_name(row: Any) -> str | None:
        extra_data = getattr(row, "extra_data", None)
        if isinstance(extra_data, dict):
            value = str(extra_data.get("account_name") or "").strip()
            if value:
                return value
        value = str(getattr(row, "author_name", "") or "").strip()
        return value or None

    @staticmethod
    def _content_status_label(content_status: str) -> str:
        normalized = str(content_status or "").strip().lower()
        if normalized == "published":
            return "已发布"
        if normalized == "deleted":
            return "已删除"
        return "待发布"

    @staticmethod
    def _build_distribution_content_item_v2(
        row: Any,
        *,
        account_map: dict[int, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        platform_code = str(getattr(row, "platform_code", "") or "").strip().lower()
        content_id = str(getattr(row, "content_id", "") or "").strip()
        title = str(getattr(row, "title", "") or content_id or "未命名内容").strip()
        view_count = DistributionService._safe_int(getattr(row, "view_count", 0))
        liked_count = DistributionService._safe_int(getattr(row, "liked_count", 0))
        comment_count = DistributionService._safe_int(getattr(row, "comment_count", 0))
        share_count = DistributionService._safe_int(getattr(row, "share_count", 0))
        published_at_raw = getattr(row, "published_at", None)
        collected_at_raw = getattr(row, "last_synced_at", None)
        content_status = str(getattr(row, "content_status", "") or "published").strip().lower()
        account_id = DistributionService._safe_int(getattr(row, "account_id", None)) or None
        account_meta = (account_map or {}).get(account_id or 0, {})
        account_name = (
            str(account_meta.get("account_name") or "").strip()
            or DistributionService._extract_content_account_name(row)
        )
        return {
            "relation_id": DistributionService._safe_int(getattr(row, "id", None)) or None,
            "account_id": account_id,
            "account_name": account_name or None,
            "account_avatar_url": str(account_meta.get("avatar_url") or "").strip() or None,
            "platform_code": platform_code,
            "platform_name": DistributionService._platform_content_display_name(platform_code),
            "content_id": content_id,
            "title": title,
            "description": DistributionService._extract_content_description(getattr(row, "extra_data", None)),
            "content_kind": str(getattr(row, "content_type", "") or "video"),
            "cover_url": str(getattr(row, "cover_url", "") or "").strip() or None,
            "content_url": str(getattr(row, "content_url", "") or "").strip() or None,
            "author_name": str(getattr(row, "author_name", "") or "").strip() or None,
            "status": content_status,
            "status_label": DistributionService._content_status_label(content_status),
            "published_at": published_at_raw.isoformat() if published_at_raw else None,
            "view_count": view_count,
            "liked_count": liked_count,
            "comment_count": comment_count,
            "share_count": share_count,
            "collected_at": collected_at_raw.isoformat() if collected_at_raw else None,
        }

    def _load_account_meta_map(self, *, user_id: int, account_ids: list[int]) -> dict[int, dict[str, Any]]:
        normalized_ids = sorted({int(account_id) for account_id in account_ids if int(account_id) > 0})
        if not normalized_ids:
            return {}

        with self.session_factory() as session:
            rows = (
                session.query(PlatformAccount)
                .filter(
                    PlatformAccount.owner_user_id == int(user_id),
                    PlatformAccount.is_deleted == 0,
                    PlatformAccount.id.in_(normalized_ids),
                )
                .all()
            )
            return {
                int(row.id): {
                    "account_name": str(row.nickname or row.account_name or "").strip() or None,
                    "avatar_url": str(row.avatar_url or "").strip() or None,
                }
                for row in rows
            }

    @staticmethod
    def _platform_content_display_name(platform_code: str) -> str:
        return {
            "douyin": "抖音",
            "dy": "抖音",
            "xiaohongshu": "小红书",
            "xhs": "小红书",
            "bilibili": "Bilibili",
            "bili": "Bilibili",
            "kuaishou": "快手",
            "ks": "快手",
        }.get(platform_code, platform_code or "未知平台")

    @staticmethod
    def _safe_int(value: Any) -> int:
        try:
            return int(float(value or 0))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _hash_json_payload(payload: Any) -> str | None:
        if payload in (None, "", [], {}):
            return None
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        return sha256_text(encoded)

    @staticmethod
    def _infer_cookie_expire_at(cookies: list[dict[str, Any]]) -> datetime | None:
        max_expire: float | None = None
        for item in cookies:
            if not isinstance(item, dict):
                continue
            raw_expire = item.get("expires", item.get("expiry"))
            try:
                expire_value = float(raw_expire)
            except (TypeError, ValueError):
                continue
            if expire_value <= 0:
                continue
            if max_expire is None or expire_value > max_expire:
                max_expire = expire_value

        if max_expire is None:
            return None

        try:
            return datetime.fromtimestamp(max_expire)
        except (TypeError, ValueError, OSError, OverflowError):
            return None

    @staticmethod
    def _platform_type_to_main_platform(platform_type: int) -> str:
        mapping = {
            1: "xiaohongshu",
            2: "bilibili",
            3: "douyin",
            4: "kuaishou",
        }
        resolved = mapping.get(int(platform_type))
        if not resolved:
            raise ContractError("当前主程序暂未接入该平台的账号映射", status_code=400)
        return resolved

    @staticmethod
    def _platform_display_name(platform_type: int) -> str:
        return {
            1: "小红书",
            2: "B站",
            3: "抖音",
            4: "快手",
        }.get(int(platform_type), str(platform_type))
