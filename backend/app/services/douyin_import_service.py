from __future__ import annotations

from datetime import datetime
from typing import Any


class DouyinImportService:
    def normalize_crawl_item(
        self,
        *,
        task_no: str,
        keyword: str,
        raw_item: dict[str, Any],
        forced_content_kind: str,
        source_scene: str = "keyword_search",
    ) -> dict[str, Any] | None:
        content_id = _safe_str(raw_item.get("content_id")) or _safe_str(_get(raw_item, "raw_data.aweme_info.aweme_id"))
        if not content_id:
            return None

        inferred_kind = forced_content_kind if forced_content_kind in {"image", "video"} else self.detect_content_kind(raw_item)
        if inferred_kind not in {"image", "video"}:
            return None

        return {
            "taskNo": task_no,
            "platformCode": "douyin",
            "keyword": keyword,
            "contentKind": inferred_kind,
            "sourceScene": source_scene,
            "contentId": content_id,
            "title": _safe_str(raw_item.get("title")),
            "summary": _safe_str(raw_item.get("desc")),
            "coverUrl": _safe_str(raw_item.get("cover_url")),
            "authorName": _safe_str(raw_item.get("author_name")),
            "authorId": _safe_str(raw_item.get("author_id")),
            "publishTime": _safe_str(raw_item.get("publish_time")),
            "likes": _safe_int(raw_item.get("like_count")),
            "comments": _safe_int(raw_item.get("comment_count")),
            "collects": _safe_int(raw_item.get("collect_count")),
            "shares": _safe_int(raw_item.get("share_count")),
            "views": _safe_int(_get(raw_item, "raw_data.aweme_info.statistics.play_count")),
            "sourceUrl": _safe_str(raw_item.get("content_url")),
            "sourceType": source_scene,
            "rawJson": raw_item,
            "crawledAt": _safe_str(raw_item.get("crawled_at")),
        }

    def detect_content_kind(self, item: dict[str, Any]) -> str:
        raw_aweme = _get(item, "raw_data.aweme_info") or {}
        images = raw_aweme.get("images")
        if isinstance(images, list) and images:
            return "image"
        image_infos = raw_aweme.get("image_infos")
        if isinstance(image_infos, list) and image_infos:
            return "image"
        if raw_aweme.get("video"):
            return "video"
        if item.get("video_url"):
            return "video"
        return "image"

    def build_image_material_payload(
        self,
        *,
        task_id: int,
        source_rank: int | None,
        cached_item: dict[str, Any],
        imported_at: datetime,
        source_ref_no: str,
    ) -> dict[str, Any]:
        raw_aweme = _get(cached_item, "rawJson.raw_data.aweme_info") or {}
        author = raw_aweme.get("author") or {}
        music = raw_aweme.get("music") or {}
        images = raw_aweme.get("images") or []
        media_entries = []
        for image in images:
            media_entries.append(
                {
                    "uri": image.get("uri"),
                    "url_list": image.get("url_list") or [],
                    "download_url_list": image.get("download_url_list") or [],
                    "height": image.get("height"),
                    "width": image.get("width"),
                }
            )

        return {
            "task_id": task_id,
            "platform": "douyin",
            "content_kind": "image",
            "keyword": cached_item.get("keyword"),
            "source_rank": source_rank,
            "content_id": cached_item.get("contentId"),
            "aweme_id": _safe_str(raw_aweme.get("aweme_id")) or cached_item.get("contentId"),
            "title": cached_item.get("title"),
            "desc": cached_item.get("summary"),
            "author_name": cached_item.get("authorName"),
            "author_id": cached_item.get("authorId"),
            "author_sec_uid": _safe_str(author.get("sec_uid")),
            "author_avatar_url": _safe_str(_get(author, "avatar_thumb.url_list.0")),
            "publish_at": _to_datetime(cached_item.get("publishTime")),
            "content_url": cached_item.get("sourceUrl"),
            "cover_url": cached_item.get("coverUrl"),
            "like_count": _safe_int(cached_item.get("likes")),
            "comment_count": _safe_int(cached_item.get("comments")),
            "collect_count": _safe_int(cached_item.get("collects")),
            "share_count": _safe_int(cached_item.get("shares")),
            "play_count": _safe_int(cached_item.get("views")),
            "media_count": len(media_entries),
            "media_json": media_entries,
            "tag_list_json": self._extract_tags(raw_aweme),
            "music_title": _safe_str(music.get("title")),
            "music_url": _safe_str(_get(music, "play_url.url_list.0")),
            "location_text": _safe_str(_get(raw_aweme, "poi_info.poi_name")),
            "extra_json": {"sourceScene": cached_item.get("sourceScene"), "sourceRefNo": source_ref_no},
            "raw_json": cached_item.get("rawJson"),
            "crawled_at": _to_datetime(cached_item.get("crawledAt")),
            "imported_at": imported_at,
            "record_status": "active",
        }

    def build_video_material_payload(
        self,
        *,
        task_id: int,
        source_rank: int | None,
        cached_item: dict[str, Any],
        imported_at: datetime,
        source_ref_no: str,
    ) -> dict[str, Any]:
        raw_aweme = _get(cached_item, "rawJson.raw_data.aweme_info") or {}
        author = raw_aweme.get("author") or {}
        music = raw_aweme.get("music") or {}
        video = raw_aweme.get("video") or {}
        bit_rate_item = _first_item(video.get("bit_rate"))
        duration_raw = video.get("duration")
        duration_sec = None
        if duration_raw is not None:
            duration_sec = int(duration_raw / 1000) if int(duration_raw) > 1000 else int(duration_raw)

        media_json = {
            "play_addr": video.get("play_addr"),
            "download_addr": video.get("download_addr"),
            "cover": video.get("cover"),
            "dynamic_cover": video.get("dynamic_cover"),
            "origin_cover": video.get("origin_cover"),
            "ratio": video.get("ratio"),
        }

        return {
            "task_id": task_id,
            "platform": "douyin",
            "content_kind": "video",
            "keyword": cached_item.get("keyword"),
            "source_rank": source_rank,
            "content_id": cached_item.get("contentId"),
            "aweme_id": _safe_str(raw_aweme.get("aweme_id")) or cached_item.get("contentId"),
            "title": cached_item.get("title"),
            "desc": cached_item.get("summary"),
            "author_name": cached_item.get("authorName"),
            "author_id": cached_item.get("authorId"),
            "author_sec_uid": _safe_str(author.get("sec_uid")),
            "author_avatar_url": _safe_str(_get(author, "avatar_thumb.url_list.0")),
            "publish_at": _to_datetime(cached_item.get("publishTime")),
            "content_url": cached_item.get("sourceUrl"),
            "cover_url": cached_item.get("coverUrl"),
            "like_count": _safe_int(cached_item.get("likes")),
            "comment_count": _safe_int(cached_item.get("comments")),
            "collect_count": _safe_int(cached_item.get("collects")),
            "share_count": _safe_int(cached_item.get("shares")),
            "play_count": _safe_int(cached_item.get("views")),
            "duration_sec": duration_sec,
            "video_width": _safe_int(video.get("width"), default=None),
            "video_height": _safe_int(video.get("height"), default=None),
            "fps": _safe_float(bit_rate_item.get("FPS")),
            "bit_rate": _safe_int(bit_rate_item.get("bit_rate"), default=None),
            "file_size": _safe_int(_get(video, "play_addr.data_size"), default=None),
            "video_format": "mp4",
            "video_url": _safe_str(cached_item.get("rawJson.video_url"))
            or _safe_str(_get(video, "play_addr.url_list.0"))
            or _safe_str(cached_item.get("sourceUrl")),
            "dynamic_cover_url": _safe_str(_get(video, "dynamic_cover.url_list.0")),
            "media_json": media_json,
            "tag_list_json": self._extract_tags(raw_aweme),
            "music_title": _safe_str(music.get("title")),
            "music_url": _safe_str(_get(music, "play_url.url_list.0")),
            "location_text": _safe_str(_get(raw_aweme, "poi_info.poi_name")),
            "extra_json": {"sourceScene": cached_item.get("sourceScene"), "sourceRefNo": source_ref_no},
            "raw_json": cached_item.get("rawJson"),
            "crawled_at": _to_datetime(cached_item.get("crawledAt")),
            "imported_at": imported_at,
            "record_status": "active",
        }

    def build_chain_payload(
        self,
        *,
        owner_user_id: int,
        content_kind: str,
        material_id: int,
        task_id: int,
        cached_item: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "owner_user_id": owner_user_id,
            "content_kind": content_kind,
            "material_id": material_id,
            "task_id": task_id,
            "content_id": cached_item.get("contentId"),
            "title": cached_item.get("title"),
            "cover_url": cached_item.get("coverUrl"),
            "publish_at": _to_datetime(cached_item.get("publishTime")),
            "like_count": _safe_int(cached_item.get("likes")),
            "comment_count": _safe_int(cached_item.get("comments")),
            "collect_count": _safe_int(cached_item.get("collects")),
            "share_count": _safe_int(cached_item.get("shares")),
        }

    @staticmethod
    def _extract_tags(raw_aweme: dict[str, Any]) -> list[str]:
        tags: list[str] = []
        for item in raw_aweme.get("text_extra") or []:
            hashtag = _safe_str(item.get("hashtag_name"))
            if hashtag and hashtag not in tags:
                tags.append(hashtag)
        return tags


def _get(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                idx = int(part)
            except ValueError:
                return None
            if idx < 0 or idx >= len(current):
                return None
            current = current[idx]
        else:
            return None
    return current


def _first_item(value: Any) -> dict[str, Any]:
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, dict):
            return first
    return {}


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _safe_int(value: Any, default: int | None = 0) -> int | None:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
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
        try:
            return datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

