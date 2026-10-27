import json
import logging
import pickle
import re
from typing import Any

from redis import Redis
from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from ..models.user_content import UserContentRelation
from .task_repository import TaskRepository

logger = logging.getLogger(__name__)


class ContentRepository:
    def __init__(
        self,
        db: Session,
        redis_client: Redis,
        *,
        redis_binary_client: Redis | None = None,
        task_repository: TaskRepository | None = None,
    ):
        self.db = db
        self.redis = redis_client
        self.redis_binary = redis_binary_client or redis_client
        self.task_repository = task_repository

    def get_staging_key(self, task_id: str) -> str:
        return f"mediacrawler:staging:{task_id}"

    def _normalize_platform(self, platform: str | None) -> str:
        p = str(platform or "").lower().strip()
        mapping = {
            "douyin": "dy",
            "dy": "dy",
            "xiaohongshu": "xhs",
            "xhs": "xhs",
            "weibo": "wb",
            "wb": "wb",
            "bilibili": "bili",
            "bili": "bili",
            "kuaishou": "ks",
            "ks": "ks",
        }
        return mapping.get(p, p)

    async def get_staging_results(self, task_id: str) -> list[dict[str, Any]]:
        task_record = self.task_repository.get(task_id) if self.task_repository else None
        platform = self._normalize_platform(task_record.platform if task_record else "dy")

        checkpoint_ids = self._load_checkpoint_note_ids(task_id=task_id, platform=platform)
        if checkpoint_ids and platform in {"dy", "xhs", "bili", "ks"}:
            rows = self._query_platform_rows_by_ids(platform=platform, content_ids=checkpoint_ids)
            logger.info(
                "[ContentRepo] Loaded %s %s rows from checkpoint task_id=%s",
                len(rows),
                platform,
                task_id,
            )
            return rows

        return self._get_staging_results_legacy(task_id)

    async def collect_content(
        self,
        user_id: int,
        task_id: str,
        platform: str,
        selected_ids: list[str],
    ) -> int:
        norm_platform = self._normalize_platform(platform)
        selected_raw = [str(item).strip() for item in selected_ids if str(item).strip()]
        if not selected_raw:
            return 0

        final_selected_ids: list[str] = []
        internal_ids: list[int] = []
        for sid in selected_raw:
            if sid.isdigit() and len(sid) < 15:
                internal_ids.append(int(sid))
            else:
                final_selected_ids.append(sid)

        if internal_ids:
            table = self._platform_table(norm_platform)
            id_col = self._platform_external_id_column(norm_platform)
            sql = text(f"SELECT `{id_col}` FROM `{table}` WHERE `id` IN :ids").bindparams(
                bindparam("ids", expanding=True)
            )
            rows = self.db.execute(sql, {"ids": internal_ids}).fetchall()
            for row in rows:
                if row[0]:
                    final_selected_ids.append(str(row[0]))

        if not final_selected_ids:
            logger.warning("[ContentRepo] No valid platform IDs found for selected: %s", selected_raw)
            return 0

        checkpoint_ids = self._load_checkpoint_note_ids(task_id=task_id, platform=norm_platform)
        if checkpoint_ids and norm_platform in {"dy", "xhs", "bili", "ks"}:
            allowed_ids = set(checkpoint_ids)
            selected_in_checkpoint = [item for item in final_selected_ids if item in allowed_ids]
            if not selected_in_checkpoint:
                logger.warning(
                    "[ContentRepo] Selected ids are not in checkpoint task_id=%s selected=%s allowed_sample=%s",
                    task_id,
                    final_selected_ids[:3],
                    list(allowed_ids)[:3],
                )
                return 0

            relation_col = self._relation_column(norm_platform)
            count = 0
            for content_id in selected_in_checkpoint:
                created = await self._create_relation(
                    user_id,
                    norm_platform,
                    relation_col,
                    content_id,
                    task_id,
                )
                if created:
                    count += 1
            return count

        return await self._collect_from_staging_legacy(
            user_id=user_id,
            task_id=task_id,
            platform=platform,
            selected_ids=selected_raw,
        )

    async def collect_detail_url_result(
        self,
        *,
        user_id: int,
        task_id: str,
        platform: str,
        url: str,
    ) -> dict[str, Any]:
        norm_platform = self._normalize_platform(platform)
        if norm_platform != "dy":
            raise ValueError(f"Unsupported platform for URL collect: {platform}")

        task_record = self.task_repository.get(task_id) if self.task_repository else None
        if task_record and task_record.user_id != user_id:
            raise PermissionError("Task does not belong to current user")

        aweme_id = self._extract_douyin_aweme_id(url)
        if not aweme_id:
            raise ValueError("无法从抖音链接中识别视频/图文 ID")

        row = self._query_platform_content(norm_platform, aweme_id)
        if not row:
            return {
                "collectedCount": 0,
                "contentId": aweme_id,
                "chainId": None,
                "contentKind": None,
                "reason": "content_not_found",
            }

        relation_col = self._relation_column(norm_platform)
        created = await self._create_relation(user_id, norm_platform, relation_col, aweme_id, task_id)
        relation_id = self._find_relation_id(
            user_id=user_id,
            platform=norm_platform,
            relation_col=relation_col,
            original_id=aweme_id,
        )
        return {
            "collectedCount": 1 if created else 0,
            "contentId": aweme_id,
            "chainId": str(relation_id) if relation_id else None,
            "contentKind": "image" if str(row.get("aweme_type")) == "68" else "video",
            "duplicated": not created,
        }

    @staticmethod
    def _extract_douyin_aweme_id(url: str) -> str:
        text = str(url or "").strip()
        if not text:
            return ""
        for pattern in (r"/(?:video|note)/(\d{10,30})", r"[?&](?:modal_id|aweme_id|group_id)=(\d{10,30})"):
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        match = re.search(r"(?<!\d)(7\d{15,25})(?!\d)", text)
        return match.group(1) if match else ""

    def _query_platform_content(self, platform: str, original_id: str) -> dict[str, Any] | None:
        table = self._platform_table(platform)
        query_sql, params = self._build_platform_content_lookup_sql(
            table=table,
            platform=platform,
            content_id=original_id,
        )
        self._reset_session_snapshot()
        try:
            row = self.db.execute(query_sql, params).mappings().first()
            return dict(row) if row else None
        finally:
            self._reset_session_snapshot()

    def _find_relation_id(
        self,
        *,
        user_id: int,
        platform: str,
        relation_col: str,
        original_id: str,
    ) -> int | None:
        self._reset_session_snapshot()
        try:
            relation = (
                self.db.query(UserContentRelation)
                .filter(
                    UserContentRelation.user_id == user_id,
                    UserContentRelation.platform == platform,
                    getattr(UserContentRelation, relation_col) == original_id,
                )
                .first()
            )
            return int(relation.id) if relation else None
        finally:
            self._reset_session_snapshot()

    def _get_staging_results_legacy(self, task_id: str) -> list[dict[str, Any]]:
        key = self.get_staging_key(task_id)
        items_raw = self.redis.lrange(key, 0, -1)
        results = []
        for item_raw in items_raw:
            try:
                item_text = item_raw.decode("utf-8") if isinstance(item_raw, bytes) else item_raw
                results.append(json.loads(item_text))
            except Exception:
                continue
        logger.info("[ContentRepo] Pulled %s items from legacy staging key: %s", len(results), key)
        return results

    async def _collect_from_staging_legacy(
        self,
        *,
        user_id: int,
        task_id: str,
        platform: str,
        selected_ids: list[str],
    ) -> int:
        key = self.get_staging_key(task_id)
        items_raw = self.redis.lrange(key, 0, -1)
        norm_platform = self._normalize_platform(platform)

        id_field_map = {
            "dy": "aweme_id",
            "xhs": "note_id",
            "bili": "bvid",
            "ks": "video_id",
            "wb": "note_id",
            "tieba": "note_id",
            "zhihu": "content_id",
        }
        id_field = id_field_map.get(norm_platform)
        if not id_field:
            logger.error("[ContentRepo] Unsupported platform: %s (normalized: %s)", platform, norm_platform)
            raise ValueError(f"Unsupported platform: {platform}")

        relation_col = self._relation_column(norm_platform)
        count = 0
        processed_item_strs = []
        for item_raw in items_raw:
            item_str = item_raw.decode("utf-8") if isinstance(item_raw, bytes) else item_raw
            item = json.loads(item_str)
            original_id = str(item.get(id_field))

            if original_id in selected_ids:
                target_table = item.get("_target_table", f"{platform}_content")
                save_item = {k: v for k, v in item.items() if not k.startswith("_")}

                await self._upsert_platform_table(target_table, save_item, id_field, original_id)

                created = await self._create_relation(user_id, norm_platform, relation_col, original_id, task_id)
                processed_item_strs.append(item_raw)
                if created:
                    count += 1

        if processed_item_strs:
            for item_raw in processed_item_strs:
                self.redis.lrem(key, 0, item_raw)
            logger.info(
                "[ContentRepo] %s items removed from legacy staging key %s after successful collection.",
                len(processed_item_strs),
                key,
            )

        return count

    def _resolve_checkpoint_key(self, *, task_id: str, platform: str) -> str:
        task_record = self.task_repository.get(task_id) if self.task_repository else None
        config = dict(task_record.config or {}) if task_record else {}
        checkpoint_key = str(config.get("checkpoint_key") or "").strip()
        if checkpoint_key:
            return checkpoint_key

        checkpoint_id = str(config.get("checkpoint_id") or "").strip()
        if checkpoint_id:
            parts = checkpoint_id.split("_")
            if len(parts) >= 3:
                return f"checkpoint:{parts[0]}:{parts[1]}:{checkpoint_id}"
            return f"checkpoint:{checkpoint_id}"

        crawler_type = str(config.get("crawler_type") or "search").strip().lower() or "search"
        return f"checkpoint:{platform}:{crawler_type}:{platform}_{crawler_type}_{task_id}"

    def _load_checkpoint_note_ids(self, task_id: str, platform: str) -> list[str]:
        checkpoint_key = self._resolve_checkpoint_key(task_id=task_id, platform=platform)
        try:
            raw = self.redis_binary.get(checkpoint_key)
        except Exception as exc:
            logger.error(
                "[ContentRepo] Redis connection error while reading checkpoint key=%s error=%s",
                checkpoint_key,
                exc,
                exc_info=True,
            )
            return []

        if not raw:
            logger.warning("[ContentRepo] Checkpoint key not found (empty): %s", checkpoint_key)
            return []

        try:
            checkpoint = self._deserialize_checkpoint(raw)
            notes = self._checkpoint_get(checkpoint, "crawled_note_list") or []
            note_ids: list[str] = []
            for note in notes:
                note_id = self._checkpoint_get(note, "note_id")
                if not note_id:
                    continue
                is_success = self._checkpoint_get(note, "is_success_crawled")
                if is_success is False:
                    continue
                note_id_text = str(note_id).strip()
                if note_id_text and note_id_text not in note_ids:
                    note_ids.append(note_id_text)
            logger.info(
                "[ContentRepo] Loaded %s note ids from checkpoint key=%s",
                len(note_ids),
                checkpoint_key,
            )
            return note_ids
        except Exception as exc:
            logger.exception("[ContentRepo] Checkpoint decode failed key=%s error=%s", checkpoint_key, exc)
            return []

    @staticmethod
    def _deserialize_checkpoint(raw: Any) -> Any:
        if isinstance(raw, (bytes, bytearray)):
            try:
                return pickle.loads(raw)
            except Exception:
                text_value = raw.decode("utf-8")
                return json.loads(text_value)
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except Exception:
                return pickle.loads(raw.encode("latin1"))
        return raw

    @staticmethod
    def _checkpoint_get(value: Any, key: str) -> Any:
        if isinstance(value, dict):
            return value.get(key)
        if hasattr(value, "model_dump"):
            return value.model_dump().get(key)
        return getattr(value, key, None)

    def _query_platform_rows_by_ids(self, *, platform: str, content_ids: list[str]) -> list[dict[str, Any]]:
        ordered_ids = [str(item).strip() for item in content_ids if str(item).strip()]
        if not ordered_ids:
            return []

        table = self._platform_table(platform)
        id_col = self._platform_external_id_column(platform)
        self._reset_session_snapshot()
        try:
            stmt = text(f"SELECT * FROM `{table}` WHERE `{id_col}` IN :ids").bindparams(
                bindparam("ids", expanding=True)
            )
            result = self.db.execute(stmt, {"ids": ordered_ids})
            rows = [dict(row._mapping) for row in result]
            rows_by_id = {str(row.get(id_col)): row for row in rows if row.get(id_col)}
            ordered_rows: list[dict[str, Any]] = []
            for item in ordered_ids:
                row = rows_by_id.get(item)
                if not row:
                    continue
                content_id = str(row.get(id_col) or "").strip()
                if content_id:
                    row["contentId"] = content_id
                    row["platformCode"] = platform
                    row["contentKind"] = self._infer_content_kind(platform, row)
                ordered_rows.append(row)
            return ordered_rows
        finally:
            self._reset_session_snapshot()

    @staticmethod
    def _relation_column(platform: str) -> str:
        relation_col_map = {
            "dy": "dy_aweme_id",
            "xhs": "xhs_note_id",
            "wb": "wb_note_id",
            "tieba": "tieba_note_id",
            "bili": "bili_video_id",
            "ks": "ks_video_id",
            "zhihu": "zhihu_content_id",
        }
        relation_col = relation_col_map.get(platform)
        if not relation_col:
            raise ValueError(f"Unsupported platform: {platform}")
        return relation_col

    @staticmethod
    def _platform_table(platform: str) -> str:
        table_map = {
            "dy": "douyin_aweme",
            "xhs": "xhs_note",
            "wb": "weibo_note",
            "tieba": "tieba_note",
            "bili": "bilibili_video",
            "ks": "kuaishou_video",
            "zhihu": "zhihu_content",
        }
        table = table_map.get(platform)
        if not table:
            raise ValueError(f"Unsupported platform: {platform}")
        return table

    @staticmethod
    def _platform_id_column(platform: str) -> str:
        id_col_map = {
            "dy": "aweme_id",
            "xhs": "note_id",
            "wb": "note_id",
            "tieba": "note_id",
            "bili": "video_id",
            "ks": "video_id",
            "zhihu": "content_id",
        }
        id_col = id_col_map.get(platform)
        if not id_col:
            raise ValueError(f"Unsupported platform: {platform}")
        return id_col

    @staticmethod
    def _platform_external_id_column(platform: str) -> str:
        id_col_map = {
            "dy": "aweme_id",
            "xhs": "note_id",
            "wb": "note_id",
            "tieba": "note_id",
            "bili": "bvid",
            "ks": "video_id",
            "zhihu": "content_id",
        }
        id_col = id_col_map.get(platform)
        if not id_col:
            raise ValueError(f"Unsupported platform: {platform}")
        return id_col

    def _build_platform_content_lookup_sql(
        self,
        *,
        table: str,
        platform: str,
        content_id: str,
    ) -> tuple[Any, dict[str, Any]]:
        external_id_col = self._platform_external_id_column(platform)
        internal_id_col = self._platform_id_column(platform)
        if platform == "bili":
            return (
                text(
                    f"""
                    SELECT * FROM `{table}`
                    WHERE `{external_id_col}` = :content_id OR `{internal_id_col}` = :content_id
                    """
                ),
                {"content_id": content_id},
            )
        return (
            text(f"SELECT * FROM `{table}` WHERE `{external_id_col}` = :content_id"),
            {"content_id": content_id},
        )

    def _relation_join_condition(self, platform: str, relation_col: str) -> str:
        external_id_col = self._platform_external_id_column(platform)
        internal_id_col = self._platform_id_column(platform)
        if platform == "bili":
            return (
                f"(t.`{external_id_col}` = r.`{relation_col}` "
                f"OR t.`{internal_id_col}` = r.`{relation_col}`)"
            )
        return f"t.`{external_id_col}` = r.`{relation_col}`"

    async def _upsert_platform_table(self, table: str, item: dict[str, Any], id_field: str, original_id: str):
        columns = list(item.keys())
        col_str = ", ".join([f"`{c}`" for c in columns])
        placeholders = ", ".join([f":{c}" for c in columns])
        update_str = ", ".join([f"`{c}`=VALUES(`{c}`)" for c in columns if c != id_field])

        sql = text(
            f"""
            INSERT INTO `{table}` ({col_str})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {update_str}
        """
        )

        self.db.execute(sql, item)
        self.db.commit()

    async def _create_relation(
        self,
        user_id: int,
        platform: str,
        relation_col: str,
        original_id: str,
        task_id: str,
    ) -> bool:
        self._reset_session_snapshot()

        column_map = {
            "dy": "dy_aweme_id",
            "xhs": "xhs_note_id",
            "wb": "wb_note_id",
            "tieba": "tieba_note_id",
            "bili": "bili_video_id",
            "ks": "ks_video_id",
            "zhihu": "zhihu_content_id",
        }
        specific_col = column_map.get(platform, relation_col)

        from sqlalchemy import or_

        q = self.db.query(UserContentRelation).filter(
            UserContentRelation.user_id == user_id,
            UserContentRelation.platform == platform,
        )
        existing = q.filter(
            or_(
                getattr(UserContentRelation, relation_col) == original_id,
                getattr(UserContentRelation, specific_col) == original_id,
            )
        ).first()

        if existing:
            self._reset_session_snapshot()
            return False

        new_rel = UserContentRelation(
            user_id=user_id,
            platform=platform,
            task_id=task_id,
        )
        setattr(new_rel, relation_col, original_id)
        if specific_col != relation_col:
            setattr(new_rel, specific_col, original_id)

        self.db.add(new_rel)
        try:
            self.db.commit()
            return True
        except Exception as exc:
            logger.error("[ContentRepo] Failed to create relation: %s", exc)
            self.db.rollback()
            return False
        finally:
            self._reset_session_snapshot()

    async def get_user_content(self, user_id: int, platform: str, content_kind: str | None = None) -> list[dict[str, Any]]:
        norm_platform = self._normalize_platform(platform)
        table = self._platform_table(norm_platform)
        id_field = self._platform_external_id_column(norm_platform)
        relation_col = self._relation_column(norm_platform)

        where_clauses = ["r.user_id = :user_id", "r.platform = :platform"]
        params = {"user_id": user_id, "platform": norm_platform}

        if norm_platform == "dy" and content_kind:
            aweme_type = "68" if content_kind == "image" else "0"
            where_clauses.append("t.aweme_type = :aweme_type")
            params["aweme_type"] = aweme_type
        elif norm_platform in {"bili", "ks"} and content_kind == "image":
            return []
        elif norm_platform == "xhs" and content_kind:
            note_type = "video" if content_kind == "video" else "normal"
            where_clauses.append("COALESCE(NULLIF(t.`type`, ''), 'normal') = :note_type")
            params["note_type"] = note_type

        join_condition = self._relation_join_condition(norm_platform, relation_col)
        where_str = " AND ".join(where_clauses)
        sql = text(
            f"""
            SELECT t.*, r.id AS chainId, r.id AS chain_id
            FROM `{table}` t
            JOIN user_content_relations r ON {join_condition}
            WHERE {where_str}
        """
        )

        self._reset_session_snapshot()
        result = self.db.execute(sql, params)
        try:
            rows = [dict(row._mapping) for row in result]
            for row in rows:
                content_id = row.get(id_field)
                if content_id:
                    row["contentId"] = str(content_id)
                row["platformCode"] = norm_platform
                row["contentKind"] = self._infer_content_kind(norm_platform, row)
            return rows
        finally:
            self._reset_session_snapshot()

    async def delete_user_content_relation(self, *, user_id: int, relation_id: int) -> bool:
        self._reset_session_snapshot()
        try:
            relation = (
                self.db.query(UserContentRelation)
                .filter(
                    UserContentRelation.id == relation_id,
                    UserContentRelation.user_id == user_id,
                )
                .first()
            )
            if not relation:
                return False
            self.db.delete(relation)
            self.db.commit()
            return True
        except Exception as exc:
            logger.error("[ContentRepo] Failed to delete relation id=%s user_id=%s: %s", relation_id, user_id, exc)
            self.db.rollback()
            raise
        finally:
            self._reset_session_snapshot()

    async def get_content_detail(
        self,
        *,
        content_id: str,
        platform_code: str,
        content_kind: str,
        source_scene: str | None = None,
        source_ref_no: str | None = None,
    ) -> dict[str, Any] | None:
        norm_platform = self._normalize_platform(platform_code)
        table = self._platform_table(norm_platform)
        id_col = self._platform_external_id_column(norm_platform)

        if content_id.isdigit() and len(content_id) < 15:
            sql = text(f"SELECT * FROM `{table}` WHERE `id` = :cid")
            params = {"cid": content_id}
        else:
            sql, params = self._build_platform_content_lookup_sql(
                table=table,
                platform=norm_platform,
                content_id=content_id,
            )

        self._reset_session_snapshot()
        row = self.db.execute(sql, params).mappings().first()
        try:
            if not row:
                return None

            data = dict(row)
            content_url = (
                data.get("aweme_url")
                or data.get("content_url")
                or data.get("note_url")
                or data.get("video_url")
            )
            cover_url = data.get("cover_url") or data.get("video_cover_url") or data.get("cover")
            download_url = (
                data.get("video_download_url")
                or data.get("download_url")
                or data.get("play_url")
                or data.get("video_play_url")
                or data.get("video_url")
            )
            publish_time = str(
                data.get("create_time")
                or data.get("publish_time")
                or data.get("time")
                or ""
            )
            resolved_kind = self._infer_content_kind(norm_platform, data)
            return {
                "id": data.get("id"),
                "contentId": data.get(id_col),
                "title": data.get("title") or data.get("desc"),
                "summary": data.get("desc") or data.get("title"),
                "cover": cover_url,
                "coverUrl": cover_url,
                "author": data.get("nickname") or data.get("author_name"),
                "authorName": data.get("nickname") or data.get("author_name"),
                "publishTime": publish_time,
                "publishAt": publish_time,
                "likes": data.get("liked_count") or data.get("likes") or 0,
                "likeCount": data.get("liked_count") or data.get("likes") or 0,
                "collects": data.get("collected_count") or data.get("collects") or 0,
                "collectCount": data.get("collected_count") or data.get("collects") or 0,
                "shares": data.get("share_count") or data.get("shares") or 0,
                "shareCount": data.get("share_count") or data.get("shares") or 0,
                "comments": data.get("comment_count") or data.get("video_comment") or data.get("comments") or 0,
                "commentCount": data.get("comment_count") or data.get("video_comment") or data.get("comments") or 0,
                "contentKind": resolved_kind or content_kind,
                "platformCode": norm_platform,
                "sourceUrl": content_url,
                "contentUrl": content_url,
                "downloadUrl": download_url,
                "videoDownloadUrl": download_url,
                "rawJson": data,
            }
        finally:
            self._reset_session_snapshot()

    @staticmethod
    def _infer_content_kind(platform: str, row: dict[str, Any]) -> str:
        if platform == "dy":
            return "image" if str(row.get("aweme_type")) == "68" else "video"
        if platform == "xhs":
            return "video" if str(row.get("type") or "").strip().lower() == "video" else "image"
        if platform in {"bili", "ks"}:
            return "video"
        return "image"

    def _reset_session_snapshot(self) -> None:
        try:
            self.db.rollback()
        except Exception as exc:  # noqa: BLE001
            logger.warning("[ContentRepo] Failed to reset DB session snapshot: %s", exc)
