from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

import httpx
from fastapi import BackgroundTasks
from redis import Redis

from app.core.config import RedisSettings
from app.core.exceptions import ContractError
from fastapi.responses import StreamingResponse
from app.db.models.douyin_data_collection import DouyinHotRankItem
from app.db.repositories.data_collection_repository import DataCollectionRepository
from app.db.repositories.content_repository import ContentRepository
from app.services.douyin_crawler_service import DouyinCrawlerService
from app.utils.redis_keys import (
    HOT_CACHE_TTL_SECONDS,
    hot_item_index_key,
    hot_item_key,
)


class DataCollectionService:
    def __init__(
        self,
        *,
        repository: DataCollectionRepository,
        content_repository: ContentRepository,
        crawler_service: DouyinCrawlerService,
        redis_settings: RedisSettings,
    ) -> None:
        self.repository = repository
        self.content_repository = content_repository
        self.crawler_service = crawler_service
        self.redis = Redis.from_url(redis_settings.url, decode_responses=True)

    def get_overview(self, *, owner_user_id: int) -> dict[str, Any]:
        stats = self.repository.get_overview_stats(owner_user_id=owner_user_id)
        platforms = self.repository.get_platform_cards(owner_user_id=owner_user_id)
        return {"stats": stats, "platforms": platforms}

    def get_platforms(self, *, owner_user_id: int) -> list[dict[str, Any]]:
        return self.repository.get_platform_cards(owner_user_id=owner_user_id)

    def get_platform_detail(self, *, owner_user_id: int, platform_code: str) -> dict[str, Any]:
        return self.repository.get_platform_detail(owner_user_id=owner_user_id, platform_code=platform_code)

    async def get_hot_ranks(
        self,
        *,
        owner_user_id: int,
        platform_code: str,
        snapshot_no: str | None,
        board_type: str | None,
        sort_by: str,
        page_no: int,
        page_size: int,
        force: bool = False,
        background_tasks: BackgroundTasks | None = None,
    ) -> dict[str, Any]:
        self._ensure_douyin_platform(platform_code)
        resolved_board_type = board_type or "hot"
        refresh_queued = False
        if snapshot_no:
            resolved_snapshot_no = snapshot_no
        else:
            resolved_snapshot_no, refresh_queued = await self._ensure_hot_snapshot(
                owner_user_id=owner_user_id,
                board_type=resolved_board_type,
                force=force,
                background_tasks=background_tasks,
            )
        data = self.repository.list_hot_rank_items(
            platform="douyin",
            board_type=resolved_board_type,
            snapshot_no=resolved_snapshot_no,
            page_no=page_no,
            page_size=page_size,
            sort_by=sort_by or "heat",
        )
        rows: list[DouyinHotRankItem] = data["list"]
        mapped: list[dict[str, Any]] = []
        for row in rows:
            mapped.append(
                self._map_hot_row(
                    owner_user_id=owner_user_id,
                    row=row,
                )
            )
        return {
            "pageNo": page_no,
            "pageSize": page_size,
            "total": data["total"],
            "list": mapped,
            "snapshotNo": data["snapshotNo"],
            "refreshing": refresh_queued,
        }

    def _ensure_douyin_platform(self, platform_code: str) -> None:
        if (platform_code or "").strip().lower() != "douyin":
            raise ContractError("仅支持 douyin 平台", status_code=400)

    async def _ensure_hot_snapshot(
        self,
        *,
        owner_user_id: int,
        board_type: str,
        force: bool = False,
        background_tasks: BackgroundTasks | None = None,
    ) -> tuple[str, bool]:
        snapshot_no, snapshot_time = self.repository.get_latest_hot_snapshot(platform="douyin", board_type=board_type)
        count = 0
        if snapshot_no:
            count = self.repository.count_hot_items_in_snapshot(platform="douyin", board_type=board_type, snapshot_no=snapshot_no)

        if force and snapshot_no and count > 0 and background_tasks is not None:
            if self._acquire_hot_refresh_lock(board_type):
                background_tasks.add_task(self._refresh_hot_snapshot_safely, board_type=board_type)
            return snapshot_no, True

        if not force and snapshot_no and snapshot_time:
            delta = datetime.now() - snapshot_time
            if delta.total_seconds() <= HOT_CACHE_TTL_SECONDS and count > 0:
                return snapshot_no, False

        return await self._refresh_hot_snapshot(board_type=board_type), False

    def _hot_refresh_lock_key(self, board_type: str) -> str:
        return f"douyin:hot_rank:refreshing:{board_type}"

    def _acquire_hot_refresh_lock(self, board_type: str) -> bool:
        try:
            return bool(self.redis.set(self._hot_refresh_lock_key(board_type), "1", ex=60, nx=True))
        except Exception:
            return True

    async def _refresh_hot_snapshot_safely(self, *, board_type: str) -> None:
        try:
            await self._refresh_hot_snapshot(board_type=board_type)
        except Exception as exc:  # noqa: BLE001
            print(f"[DouyinHot] Background refresh failed: {exc}")
        finally:
            try:
                self.redis.delete(self._hot_refresh_lock_key(board_type))
            except Exception:
                pass

    async def _refresh_hot_snapshot(self, *, board_type: str) -> str:
        try:
            snapshot_no, hot_items = await self._crawl_douyin_hot_native(board_type=board_type, limit=50)
            resolved_snapshot_no = snapshot_no
            snapshot_at = datetime.now()
            self.repository.upsert_hot_rank_items(
                platform="douyin",
                board_type=board_type,
                board_name=hot_items[0].get("board_name") if hot_items else "抖音热榜",
                snapshot_no=resolved_snapshot_no,
                snapshot_time=snapshot_at,
                items=hot_items,
            )
            self._cache_hot_items(snapshot_no=resolved_snapshot_no, hot_items=hot_items)
            return resolved_snapshot_no
        except Exception as exc:  # noqa: BLE001
            raise ContractError(f"获取热榜失败: {exc}", status_code=500) from exc

    def _cache_hot_items(self, *, snapshot_no: str, hot_items: list[dict[str, Any]]) -> None:
        try:
            index_key = hot_item_index_key(snapshot_no)
            pipe = self.redis.pipeline()
            for item in hot_items:
                rank = _safe_int(item.get("rank"))
                if rank <= 0:
                    continue
                payload = self._hot_item_payload_from_raw(snapshot_no=snapshot_no, raw_item=item)
                pipe.setex(
                    hot_item_key(snapshot_no, rank),
                    HOT_CACHE_TTL_SECONDS,
                    json.dumps(payload, ensure_ascii=False, default=str),
                )
                content_id = str(payload.get("contentId") or "").strip()
                if content_id:
                    pipe.hset(index_key, content_id, str(rank))
            pipe.expire(index_key, HOT_CACHE_TTL_SECONDS)
            pipe.execute()
        except Exception as exc:  # noqa: BLE001
            print(f"[DouyinHot] Redis cache write skipped: {exc}")

    async def _crawl_douyin_hot_native(self, board_type: str, limit: int) -> tuple[str, list[dict[str, Any]]]:
        url = "https://www.douyin.com/aweme/v1/web/hot/search/list/?device_platform=webapp&aid=6383&channel=channel_pc_web&detail_list=1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "Referer": "https://www.douyin.com/",
            "Accept": "application/json, text/plain, */*",
        }

        try:
            async with httpx.AsyncClient(timeout=20, headers=headers, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            raise ContractError(f"获取抖音热榜数据失败: {exc}") from exc

        word_list = payload.get("data", {}).get("word_list", []) or []
        snapshot_no = f"HK{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        crawled_at = datetime.now()

        result: list[dict[str, Any]] = []
        for raw in word_list[:limit]:
            try:
                word = str(raw.get("word") or "").strip()[:255]
                aweme_id = str(raw.get("aweme_id") or raw.get("group_id") or "").strip()
                if aweme_id == "0":
                    aweme_id = ""

                from urllib.parse import quote
                content_url = f"https://www.douyin.com/search/{quote(word)}" if word else None

                def _get_url(obj: Any) -> str | None:
                    if not isinstance(obj, dict):
                        return None
                    ul = obj.get("url_list")
                    return str(ul[0]) if isinstance(ul, list) and ul else None

                cover_url = _get_url(raw.get("word_cover"))
                rank = _safe_int(raw.get("position"))
                if rank <= 0:
                    rank = len(result) + 1

                event_time = None
                raw_event_time = raw.get("event_time")
                if raw_event_time:
                    try:
                        ts = int(raw_event_time)
                        if ts < 946684800000:
                            ts *= 1000
                        event_time = datetime.fromtimestamp(ts / 1000)
                    except (ValueError, TypeError):
                        pass

                title = str(raw.get("word") or "").strip()[:255]
                word = str(raw.get("word") or "").strip()[:255]

                merged = {
                    "platform": "douyin",
                    "board_type": board_type,
                    "board_name": "抖音热榜",
                    "snapshot_no": snapshot_no,
                    "rank": rank,
                    "title": title,
                    "word": word,
                    "hot_value": int(raw.get("hot_value") or 0),
                    "content_url": content_url,
                    "cover_url": cover_url,
                    "aweme_id": aweme_id or None,
                    "event_time": event_time,
                    "article_detail_count": int(raw.get("article_detail_count") or 0),
                    "discuss_video_count": int(raw.get("discuss_video_count") or 0),
                    "video_count": int(raw.get("video_count") or 0),
                    "room_count": int(raw.get("room_count") or 0),
                    "label": int(raw.get("label") or 0),
                    "label_url": _get_url(raw.get("label_url")),
                    "sentence_id": str(raw.get("sentence_id") or "")[:255],
                    "sentence_tag": int(raw.get("sentence_tag") or 0),
                    "raw_json": raw,
                    "crawled_at": crawled_at,
                }
                result.append(merged)
            except Exception as e:
                print(f"[DouyinHot] Skipping one item due to parse error: {e}")
                continue

        return snapshot_no, result

    def _map_hot_row(
        self,
        *,
        owner_user_id: int,
        row: DouyinHotRankItem,
    ) -> dict[str, Any]:
        content_id = _hot_content_id(row)
        video_count = _safe_int(row.video_count)
        discuss_video_count = _safe_int(row.discuss_video_count)
        article_detail_count = _safe_int(row.article_detail_count)
        room_count = _safe_int(row.room_count)
        source_url = _resolve_hot_source_url(hot_item=row, fallback_content_id=content_id)
        return {
            "contentId": content_id,
            "rank": int(row.rank or 0),
            "title": row.title or "",
            "summary": row.word or "",
            "cover": row.cover_url or "",
            "coverUrl": row.cover_url or "",
            "authorName": _normalize_hot_board_name(row.board_name),
            "publishTime": _fmt_dt(row.event_time) or _fmt_dt(row.snapshot_time),
            "hotValue": int(row.hot_value or 0),
            "likes": video_count,
            "comments": discuss_video_count,
            "shares": article_detail_count,
            "views": room_count,
            "tags": [row.word] if row.word else [],
            "sourceUrl": source_url,
            "sourceType": "hot_rank",
            "contentKind": _content_kind_from_hot(row),
            "platformCode": "douyin",
            "snapshotNo": row.snapshot_no,
            "articleDetailCount": article_detail_count,
            "discussVideoCount": discuss_video_count,
            "videoCount": video_count,
            "roomCount": room_count,
            "materialId": None,
            "chainId": None,
            "importStatus": "not_imported",
        }

    async def get_proxy_download_response(self, url: str, title: str | None = None) -> StreamingResponse:
        """代理资源下载并确保文件格式与名称正确"""
        import mimetypes
        import unicodedata
        from urllib.parse import quote

        content_type = "application/octet-stream"
        content_length = None
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                probe = await client.head(url)
                if probe.status_code != 200:
                    probe = await client.get(url, headers={"Range": "bytes=0-1"})

                content_type = probe.headers.get("Content-Type", content_type).split(";")[0].strip()
                content_length = probe.headers.get("Content-Length")
        except Exception:
            pass

        ext = mimetypes.guess_extension(content_type) or ""
        if not ext:
            if "webp" in content_type: ext = ".webp"
            elif "video/mp4" in content_type: ext = ".mp4"
            elif "image/jpeg" in content_type: ext = ".jpg"
            elif "image/png" in content_type: ext = ".png"

        filename = self._safe_download_filename(title or "download")

        if ext and not filename.lower().endswith(ext.lower()):
            if ext == ".bin" or not ext:
                low_url = url.lower()
                if ".webp" in low_url: ext = ".webp"
                elif ".mp4" in low_url: ext = ".mp4"

            if ext and ext != ".bin":
                filename += ext

        encoded_filename = quote(filename, safe="")
        ascii_filename = unicodedata.normalize("NFKD", filename).encode("ascii", "ignore").decode("ascii")
        ascii_filename = self._safe_download_filename(ascii_filename or "download")
        if ext and not ascii_filename.lower().endswith(ext.lower()):
            ascii_filename += ext

        async def stream_generator():
            async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        yield chunk

        headers = {
            "Content-Disposition": f"attachment; filename=\"{ascii_filename}\"; filename*=UTF-8''{encoded_filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
        if content_length and content_length.isdigit() and int(content_length) > 1:
            headers["Content-Length"] = content_length

        return StreamingResponse(
            stream_generator(),
            media_type=content_type,
            headers=headers
        )

    @staticmethod
    def _safe_download_filename(filename: str, max_length: int = 96) -> str:
        """生成可放入 Content-Disposition 的文件名主体，避免换行和控制字符污染响应头。"""
        cleaned = re.sub(r"[\x00-\x1f\x7f]+", " ", filename or "download")
        cleaned = re.sub(r'[\\/:*?"<>|]+', "_", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ._")
        if not cleaned:
            return "download"
        return cleaned[:max_length].rstrip(" ._") or "download"

    async def get_staged_results(self, *, task_id: str) -> list[dict[str, Any]]:
        """查看 Redis 暂存的数据"""
        return await self.content_repository.get_staging_results(task_id)

    async def collect_staged_content(self, *, user_id: int, task_id: str, platform: str, selected_ids: list[str]) -> int:
        """人工筛选后入库"""
        return await self.content_repository.collect_content(
            user_id=user_id,
            task_id=task_id,
            platform=platform,
            selected_ids=selected_ids
        )

    async def collect_detail_url_result(self, *, user_id: int, task_id: str, platform: str, url: str) -> dict[str, Any]:
        """detail 链接任务完成后，将已写入平台主表的内容绑定到当前用户。"""
        if not str(url or "").strip():
            raise ContractError("链接不能为空", status_code=400)
        try:
            result = await self.content_repository.collect_detail_url_result(
                user_id=user_id,
                task_id=task_id,
                platform=platform,
                url=url,
            )
        except PermissionError as exc:
            raise ContractError("无权操作该任务", status_code=403) from exc
        except ValueError as exc:
            raise ContractError(str(exc), status_code=400) from exc
        if result.get("reason") == "content_not_found":
            raise ContractError("爬虫已结束，但数据库中还没有对应内容，请稍后重试", status_code=404)
        return result

    async def get_my_content(self, *, user_id: int, platform: str, content_kind: str | None = None) -> list[dict[str, Any]]:
        """查看已关联的内容"""
        return await self.content_repository.get_user_content(
            user_id=user_id,
            platform=platform,
            content_kind=content_kind
        )

    async def delete_material_relation(self, *, user_id: int, chain_id: str) -> bool:
        """只删除用户内容关系，不删除平台内容主表数据。"""
        relation_id = _safe_int(chain_id, default=0)
        if relation_id <= 0:
            raise ContractError("素材关系ID非法", status_code=400)
        deleted = await self.content_repository.delete_user_content_relation(
            user_id=user_id,
            relation_id=relation_id,
        )
        if not deleted:
            raise ContractError("素材关系不存在", status_code=404)
        return True

    async def get_content_detail(
        self,
        *,
        content_id: str,
        platform_code: str,
        content_kind: str,
        source_scene: str | None = None,
        source_ref_no: str | None = None,
    ) -> dict[str, Any] | None:
        """获取采集结果或库内内容的详细数据"""
        detail = await self.content_repository.get_content_detail(
            content_id=content_id,
            platform_code=platform_code,
            content_kind=content_kind,
            source_scene=source_scene,
            source_ref_no=source_ref_no,
        )
        if detail:
            return detail

        if (source_scene or "").strip().lower() == "hot_rank":
            hot_row = self.repository.find_hot_item_detail(
                platform="douyin",
                content_id=content_id,
                board_type=None,
                snapshot_no=source_ref_no,
            )
            if hot_row:
                hot_item = self._map_hot_row(owner_user_id=0, row=hot_row)
                return {
                    "contentId": hot_item["contentId"],
                    "platformCode": "douyin",
                    "contentKind": hot_item["contentKind"],
                    "sourceScene": "hot_rank",
                    "sourceRefNo": hot_item.get("snapshotNo"),
                    "title": hot_item["title"],
                    "summary": hot_item["summary"],
                    "cover": hot_item.get("cover"),
                    "coverUrl": hot_item.get("coverUrl"),
                    "authorName": hot_item.get("authorName"),
                    "publishAt": hot_item.get("publishTime"),
                    "contentUrl": hot_item.get("sourceUrl"),
                    "sourceUrl": hot_item.get("sourceUrl"),
                    "likeCount": hot_item.get("likes", 0),
                    "commentCount": hot_item.get("comments", 0),
                    "shareCount": hot_item.get("shares", 0),
                    "playCount": hot_item.get("views", 0),
                    "tagList": hot_item.get("tags", []),
                    "extraJson": hot_item,
                    "rawJson": hot_row.raw_json,
                    "importStatus": "not_imported",
                }
        return None

    def _hot_item_payload_from_raw(self, *, snapshot_no: str, raw_item: dict[str, Any]) -> dict[str, Any]:
        content_id = (
            str(raw_item.get("aweme_id") or "").strip()
            or str(raw_item.get("sentence_id") or "").strip()
            or str(raw_item.get("word") or "").strip()
            or f"hot:{snapshot_no}:{_safe_int(raw_item.get('rank'))}"
        )
        aweme_id = _resolve_hot_aweme_id_from_raw(raw_item=raw_item, fallback_content_id=content_id)
        sentence_id = _resolve_hot_sentence_id_from_raw(raw_item)
        source_url = _resolve_hot_source_url_from_raw(
            raw_item=raw_item,
            fallback_content_id=content_id,
        )
        video_count = _safe_int(raw_item.get("video_count"))
        discuss_video_count = _safe_int(raw_item.get("discuss_video_count"))
        article_detail_count = _safe_int(raw_item.get("article_detail_count"))
        room_count = _safe_int(raw_item.get("room_count"))
        return {
            "taskNo": snapshot_no,
            "platformCode": "douyin",
            "keyword": None,
            "contentKind": "video" if aweme_id else "image",
            "sourceScene": "hot_rank",
            "contentId": content_id,
            "title": raw_item.get("title"),
            "summary": raw_item.get("word"),
            "coverUrl": raw_item.get("cover_url"),
            "authorName": _normalize_hot_board_name(raw_item.get("board_name")),
            "authorId": None,
            "publishTime": _fmt_dt(_to_datetime(raw_item.get("event_time"))),
            "likes": video_count,
            "comments": discuss_video_count,
            "collects": 0,
            "shares": article_detail_count,
            "views": room_count,
            "sourceUrl": source_url,
            "sourceType": "hot_rank",
            "snapshotNo": snapshot_no,
            "rank": _safe_int(raw_item.get("rank")),
            "hotValue": _safe_int(raw_item.get("hot_value")),
            "boardType": raw_item.get("board_type"),
            "boardName": _normalize_hot_board_name(raw_item.get("board_name")),
            "articleDetailCount": article_detail_count,
            "discussVideoCount": discuss_video_count,
            "videoCount": video_count,
            "roomCount": room_count,
            "awemeId": aweme_id,
            "sentenceId": sentence_id,
            "rawJson": {"raw_data": raw_item.get("raw_json") or raw_item},
            "crawledAt": _fmt_dt(_to_datetime(raw_item.get("crawled_at"))),
        }


def _sort_heat(item: dict[str, Any]) -> int:
    return (
        _safe_int(item.get("hotValue"))
        + _safe_int(item.get("likes"))
        + _safe_int(item.get("comments"))
        + _safe_int(item.get("collects"))
        + _safe_int(item.get("shares"))
        + _safe_int(item.get("views"))
    )


def _to_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass
    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _fmt_dt(value: datetime | None) -> str | None:
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else None


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_hot_board_name(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "抖音热榜"
    if "鎶栭煶" in text or "鐑" in text:
        return "抖音热榜"
    return text


def _hot_content_id(row: DouyinHotRankItem) -> str:
    raw_json = row.raw_json if isinstance(row.raw_json, dict) else {}
    group_id = str(raw_json.get("group_id") or "").strip()
    return (
        str(row.aweme_id or "").strip()
        or group_id
        or str(row.sentence_id or "").strip()
        or str(row.word or "").strip()
        or f"hot:{row.snapshot_no}:{row.rank}"
    )


def _content_kind_from_hot(row: DouyinHotRankItem) -> str:
    if str(row.aweme_id or "").strip():
        return "video"
    raw_json = row.raw_json if isinstance(row.raw_json, dict) else {}
    if str(raw_json.get("group_id") or "").strip():
        return "video"
    content_url = str(row.content_url or "").strip()
    if content_url and re.search(r"/(?:video|note)/\d+", content_url):
        return "video"
    if _safe_int(raw_json.get("video_count")) > 0:
        return "video"
    return "image"


def _resolve_hot_aweme_id_from_raw(*, raw_item: dict[str, Any], fallback_content_id: str) -> str | None:
    direct_aweme_id = str(raw_item.get("aweme_id") or "").strip()
    if direct_aweme_id:
        return direct_aweme_id
    direct_group_id = str(raw_item.get("group_id") or "").strip()
    if direct_group_id:
        return direct_group_id
    raw_json = raw_item.get("raw_json")
    if isinstance(raw_json, dict):
        nested_group_id = str(raw_json.get("group_id") or "").strip()
        if nested_group_id:
            return nested_group_id
    content_url = str(raw_item.get("content_url") or "").strip()
    if content_url:
        match = re.search(r"/(?:video|note)/(\d+)", content_url)
        if match:
            return match.group(1)
    if fallback_content_id and fallback_content_id.isdigit() and len(fallback_content_id) >= 10:
        return fallback_content_id
    return None


def _resolve_hot_sentence_id_from_raw(raw_item: dict[str, Any]) -> str | None:
    sentence_id = str(raw_item.get("sentence_id") or "").strip()
    if sentence_id:
        return sentence_id
    raw_json = raw_item.get("raw_json")
    if isinstance(raw_json, dict):
        nested_sentence_id = str(raw_json.get("sentence_id") or "").strip()
        if nested_sentence_id:
            return nested_sentence_id
    return None


def _resolve_hot_source_url(*, hot_item: DouyinHotRankItem, fallback_content_id: str) -> str | None:
    word = str(hot_item.word or "").strip()
    if word:
        from urllib.parse import quote
        return f"https://www.douyin.com/search/{quote(word)}"
    return None


def _resolve_hot_source_url_from_raw(*, raw_item: dict[str, Any], fallback_content_id: str) -> str | None:
    word = str(raw_item.get("word") or raw_item.get("title") or "").strip()
    if word:
        from urllib.parse import quote
        return f"https://www.douyin.com/search/{quote(word)}"
    return None
