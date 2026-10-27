from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, time, timedelta
from typing import Any

from sqlalchemy import asc, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.douyin_data_collection import DouyinHotRankItem
from app.db.models.platform_account import PlatformAccount, PlatformAccountAuthLog, PlatformAccountSession
from app.db.models.task import TaskModel


SUPPORTED_PLATFORM_META: dict[str, dict[str, Any]] = {
    "douyin": {
        "aliases": {"douyin", "dy"},
        "platformName": "\u6296\u97f3",
        "icon": "music_note",
        "themeColor": "text-gray-900 bg-gray-100 border-gray-200",
        "supportsContentKinds": ["image", "video"],
    },
    "xiaohongshu": {
        "aliases": {"xiaohongshu", "xhs"},
        "platformName": "\u5c0f\u7ea2\u4e66",
        "icon": "auto_awesome",
        "themeColor": "text-red-600 bg-red-50 border-red-200",
        "supportsContentKinds": ["image", "video"],
    },
    "kuaishou": {
        "aliases": {"kuaishou", "ks"},
        "platformName": "\u5feb\u624b",
        "icon": "bolt",
        "themeColor": "text-orange-600 bg-orange-50 border-orange-200",
        "supportsContentKinds": ["video"],
    },
    "bilibili": {
        "aliases": {"bilibili", "bili"},
        "platformName": "B\u7ad9",
        "icon": "tv",
        "themeColor": "text-sky-600 bg-sky-50 border-sky-200",
        "supportsContentKinds": ["video"],
    },
}


class DataCollectionRepository:
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

    @staticmethod
    def _today_range() -> tuple[datetime, datetime]:
        now = datetime.now()
        start = datetime.combine(now.date(), time.min)
        end = start + timedelta(days=1)
        return start, end

    @staticmethod
    def _resolve_hot_rank(item: dict[str, Any]) -> int:
        raw_json = item.get("raw_json")
        if isinstance(raw_json, dict):
            try:
                position_rank = int(raw_json.get("position"))
                if position_rank > 0:
                    return position_rank
            except (TypeError, ValueError):
                pass
        try:
            return int(item.get("rank") or 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _format_latest_update_time(latest_sync_at: datetime | None, *, fallback: str) -> str:
        if not latest_sync_at:
            return fallback
        diff = datetime.now() - latest_sync_at
        minutes = int(diff.total_seconds() // 60)
        if minutes < 1:
            return "刚刚"
        if minutes < 60:
            return f"{minutes}分钟前"
        return f"{int(minutes // 60)}小时前"

    def get_overview_stats(self, *, owner_user_id: int) -> dict[str, int]:
        start, end = self._today_range()
        with self.session_scope() as session:
            hot_rank_updates = (
                session.scalar(
                    select(func.count(func.distinct(DouyinHotRankItem.snapshot_no))).where(
                        DouyinHotRankItem.snapshot_time >= start,
                        DouyinHotRankItem.snapshot_time < end,
                    )
                )
                or 0
            )
            keyword_task_count = self._count_crawler_tasks(session=session, owner_user_id=owner_user_id)
            keyword_task_active = self._count_crawler_tasks(
                session=session,
                owner_user_id=owner_user_id,
                states={"created", "collecting", "parsing"},
            )
            return {
                "platformCount": len(SUPPORTED_PLATFORM_META),
                "todayFetched": 0,
                "hotRankUpdates": int(hot_rank_updates),
                "keywordTaskCount": keyword_task_count,
                "keywordTaskActive": keyword_task_active,
            }

    @staticmethod
    def _count_crawler_tasks(
        *,
        session: Session,
        owner_user_id: int,
        platform: str | None = None,
        states: set[str] | None = None,
    ) -> int:
        query = select(func.count(TaskModel.id)).where(
            TaskModel.user_id == owner_user_id,
            TaskModel.task_type.in_({"mediacrawler_collect", "crawler_collect"}),
        )
        if platform:
            aliases = SUPPORTED_PLATFORM_META.get(platform, {}).get("aliases", {platform})
            query = query.where(TaskModel.platform.in_(aliases))
        if states:
            query = query.where(TaskModel.state.in_(states))
        return int(session.scalar(query) or 0)

    def get_latest_hot_snapshot(self, *, platform: str = "douyin", board_type: str = "hot") -> tuple[str | None, datetime | None]:
        with self.session_scope() as session:
            item = session.scalar(
                select(DouyinHotRankItem)
                .where(
                    DouyinHotRankItem.platform == platform,
                    DouyinHotRankItem.board_type == board_type,
                )
                .order_by(DouyinHotRankItem.snapshot_time.desc(), DouyinHotRankItem.id.desc())
                .limit(1)
            )
            if not item:
                return None, None
            return item.snapshot_no, item.snapshot_time

    def count_hot_items_in_snapshot(self, *, platform: str, board_type: str, snapshot_no: str) -> int:
        with self.session_scope() as session:
            count = session.scalar(
                select(func.count(DouyinHotRankItem.id)).where(
                    DouyinHotRankItem.platform == platform,
                    DouyinHotRankItem.board_type == board_type,
                    DouyinHotRankItem.snapshot_no == snapshot_no,
                )
            )
            return int(count or 0)

    def get_platform_card(self, *, owner_user_id: int, platform_code: str) -> dict[str, Any]:
        platform_meta = SUPPORTED_PLATFORM_META.get(platform_code)
        if not platform_meta:
            raise ValueError(f"Unsupported platform: {platform_code}")

        hot_rank_count = 0
        latest_sync_at: datetime | None = None
        if platform_code == "douyin":
            snapshot_no, snapshot_time = self.get_latest_hot_snapshot(platform="douyin", board_type="hot")
            if snapshot_no:
                hot_rank_count = self.count_hot_items_in_snapshot(
                    platform="douyin",
                    board_type="hot",
                    snapshot_no=snapshot_no,
                )
                latest_sync_at = snapshot_time

        latest_update_time = self._format_latest_update_time(
            latest_sync_at,
            fallback="暂未同步" if platform_code != "douyin" else "暂无数据",
        )

        with self.session_scope() as session:
            keyword_task_count = self._count_crawler_tasks(
                session=session,
                owner_user_id=owner_user_id,
                platform=platform_code,
            )
            keyword_task_active = self._count_crawler_tasks(
                session=session,
                owner_user_id=owner_user_id,
                platform=platform_code,
                states={"created", "collecting", "parsing"},
            )

        return {
            "platformCode": platform_code,
            "platformName": platform_meta["platformName"],
            "icon": platform_meta["icon"],
            "latestUpdateTime": latest_update_time,
            "hotRankCount": hot_rank_count,
            "keywordTaskCount": keyword_task_count,
            "status": "collecting" if keyword_task_active > 0 else "normal",
            "themeColor": platform_meta["themeColor"],
            "lastSyncAt": latest_sync_at.strftime("%Y-%m-%d %H:%M:%S") if latest_sync_at else None,
        }

    def get_platform_cards(self, *, owner_user_id: int) -> list[dict[str, Any]]:
        return [
            self.get_platform_card(owner_user_id=owner_user_id, platform_code=platform_code)
            for platform_code in SUPPORTED_PLATFORM_META
        ]

    def get_platform_detail(self, *, owner_user_id: int, platform_code: str) -> dict[str, Any]:
        card = self.get_platform_card(owner_user_id=owner_user_id, platform_code=platform_code)
        return {
            "platformCode": card["platformCode"],
            "platformName": card["platformName"],
            "status": card["status"],
            "latestUpdateTime": card["latestUpdateTime"],
            "hotRankCount": card["hotRankCount"],
            "supportsContentKinds": SUPPORTED_PLATFORM_META[platform_code]["supportsContentKinds"],
            "lastSyncAt": card["lastSyncAt"],
        }

    def list_hot_rank_items(
        self,
        *,
        platform: str,
        board_type: str,
        snapshot_no: str | None,
        page_no: int,
        page_size: int,
        sort_by: str,
    ) -> dict[str, Any]:
        with self.session_scope() as session:
            resolved_snapshot_no = snapshot_no
            if not resolved_snapshot_no:
                resolved_snapshot_no = session.scalar(
                    select(DouyinHotRankItem.snapshot_no)
                    .where(
                        DouyinHotRankItem.platform == platform,
                        DouyinHotRankItem.board_type == board_type,
                    )
                    .order_by(DouyinHotRankItem.snapshot_time.desc(), DouyinHotRankItem.id.desc())
                    .limit(1)
                )
            if not resolved_snapshot_no:
                return {"snapshotNo": None, "total": 0, "list": []}

            query = select(DouyinHotRankItem).where(
                DouyinHotRankItem.platform == platform,
                DouyinHotRankItem.board_type == board_type,
                DouyinHotRankItem.snapshot_no == resolved_snapshot_no,
            )
            total = session.scalar(select(func.count()).select_from(query.subquery())) or 0

            if sort_by == "time":
                query = query.order_by(DouyinHotRankItem.event_time.desc(), DouyinHotRankItem.rank.asc())
            else:
                query = query.order_by(DouyinHotRankItem.hot_value.desc(), DouyinHotRankItem.rank.asc())

            rows = session.scalars(query.offset((page_no - 1) * page_size).limit(page_size)).all()
            return {
                "snapshotNo": resolved_snapshot_no,
                "total": int(total),
                "list": list(rows),
            }

    def get_platform_auth_bundle(
        self,
        *,
        auth_account_id: int,
        owner_user_id: int,
        platform_code: str,
    ) -> tuple[PlatformAccount | None, PlatformAccountSession | None]:
        with self.session_scope() as session:
            account = session.scalar(
                select(PlatformAccount).where(
                    PlatformAccount.id == auth_account_id,
                    PlatformAccount.owner_user_id == owner_user_id,
                    PlatformAccount.platform_code == platform_code,
                    PlatformAccount.is_deleted == 0,
                )
            )
            if not account:
                return None, None

            auth_session = session.scalar(
                select(PlatformAccountSession).where(
                    PlatformAccountSession.account_id == account.id,
                )
            )
            return account, auth_session

    def mark_platform_auth_need_reauth(
        self,
        *,
        auth_account_id: int,
        reason: str | None = None,
    ) -> None:
        with self.session_scope() as session:
            account = session.get(PlatformAccount, auth_account_id)
            if not account:
                return

            account.auth_status = "need_reauth"
            auth_session = session.scalar(
                select(PlatformAccountSession).where(
                    PlatformAccountSession.account_id == auth_account_id,
                )
            )
            if auth_session:
                auth_session.status = "need_reauth"
                auth_session.last_validated_at = datetime.now()

            session.add(
                PlatformAccountAuthLog(
                    account_id=auth_account_id,
                    event_type="expire",
                    event_status="failed",
                    fail_reason=(reason or "auth session invalid")[:500],
                )
            )

    def mark_platform_auth_validated(
        self,
        *,
        auth_account_id: int,
    ) -> None:
        with self.session_scope() as session:
            account = session.get(PlatformAccount, auth_account_id)
            if account and account.auth_status != "authorized":
                account.auth_status = "authorized"

            auth_session = session.scalar(
                select(PlatformAccountSession).where(
                    PlatformAccountSession.account_id == auth_account_id,
                )
            )
            if not auth_session:
                return
            auth_session.status = "active"
            auth_session.last_validated_at = datetime.now()

    def find_hot_item_detail(
        self,
        *,
        platform: str,
        content_id: str,
        board_type: str | None,
        snapshot_no: str | None,
    ) -> DouyinHotRankItem | None:
        with self.session_scope() as session:
            group_id_expr = func.json_unquote(func.json_extract(DouyinHotRankItem.raw_json, "$.group_id"))
            from sqlalchemy import or_

            query = select(DouyinHotRankItem).where(DouyinHotRankItem.platform == platform)
            if board_type:
                query = query.where(DouyinHotRankItem.board_type == board_type)
            if snapshot_no:
                query = query.where(DouyinHotRankItem.snapshot_no == snapshot_no)
            query = query.where(
                or_(
                    DouyinHotRankItem.aweme_id == content_id,
                    DouyinHotRankItem.sentence_id == content_id,
                    DouyinHotRankItem.word == content_id,
                    group_id_expr == content_id,
                )
            )
            return session.scalar(
                query.order_by(
                    DouyinHotRankItem.snapshot_time.desc(),
                    DouyinHotRankItem.rank.asc(),
                    DouyinHotRankItem.id.desc(),
                )
            )

    def upsert_hot_rank_items(
        self,
        *,
        platform: str,
        board_type: str,
        board_name: str | None,
        snapshot_no: str,
        snapshot_time: datetime,
        items: list[dict[str, Any]],
    ) -> int:
        if not items:
            return 0

        from sqlalchemy.dialects.mysql import insert

        affected = 0
        with self.session_scope() as session:
            insert_values = []
            for item in items:
                rank = self._resolve_hot_rank(item)
                if rank <= 0:
                    continue

                val = {
                    "platform": platform,
                    "board_type": board_type,
                    "board_name": board_name,
                    "snapshot_no": snapshot_no,
                    "snapshot_time": snapshot_time,
                    "rank": rank,
                    "title": (item.get("title") or "")[:255],
                    "word": (item.get("word") or "")[:255],
                    "hot_value": int(item.get("hot_value") or 0),
                    "content_url": item.get("content_url"),
                    "cover_url": item.get("cover_url"),
                    "aweme_id": item.get("aweme_id"),
                    "event_time": item.get("event_time"),
                    "article_detail_count": int(item.get("article_detail_count") or 0),
                    "discuss_video_count": int(item.get("discuss_video_count") or 0),
                    "video_count": int(item.get("video_count") or 0),
                    "room_count": int(item.get("room_count") or 0),
                    "label": item.get("label"),
                    "label_url": item.get("label_url"),
                    "sentence_id": item.get("sentence_id"),
                    "sentence_tag": item.get("sentence_tag"),
                    "raw_json": item.get("raw_json"),
                    "crawled_at": item.get("crawled_at") or datetime.now(),
                }
                insert_values.append(val)
                affected += 1

            if insert_values:
                stmt = insert(DouyinHotRankItem).values(insert_values)
                update_cols = {
                    column_name: getattr(stmt.inserted, column_name)
                    for column_name in insert_values[0].keys()
                    if column_name not in {"platform", "board_type", "snapshot_no", "rank"}
                }
                on_dup_stmt = stmt.on_duplicate_key_update(**update_cols)
                session.execute(on_dup_stmt)

        return affected

    def list_hot_for_export(self, *, platform: str, board_type: str, snapshot_no: str | None) -> list[DouyinHotRankItem]:
        with self.session_scope() as session:
            resolved_snapshot_no = snapshot_no
            if not resolved_snapshot_no:
                resolved_snapshot_no = session.scalar(
                    select(DouyinHotRankItem.snapshot_no)
                    .where(
                        DouyinHotRankItem.platform == platform,
                        DouyinHotRankItem.board_type == board_type,
                    )
                    .order_by(DouyinHotRankItem.snapshot_time.desc(), DouyinHotRankItem.id.desc())
                    .limit(1)
                )
            if not resolved_snapshot_no:
                return []
            rows = session.scalars(
                select(DouyinHotRankItem)
                .where(
                    DouyinHotRankItem.platform == platform,
                    DouyinHotRankItem.board_type == board_type,
                    DouyinHotRankItem.snapshot_no == resolved_snapshot_no,
                )
                .order_by(asc(DouyinHotRankItem.rank))
            ).all()
            return list(rows)
