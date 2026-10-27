from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from app.core.config import LoggingSettings, MediaCrawlerSettings, MySQLSettings, RedisSettings
from app.core.logging import get_logger
from app.db.repositories.task_repository import TaskRecord

from .models import MediaCrawlerJobSpec, MediaCrawlerRunResult
from .runner import MediaCrawlerRunner
from .sidecar import SignSrvSidecar, CrawlerEngineSidecar

logger = get_logger(__name__)


PLATFORM_MAP = {
    "douyin": "dy",
    "dy": "dy",
    "xiaohongshu": "xhs",
    "xhs": "xhs",
    "bilibili": "bili",
    "bili": "bili",
    "weibo": "wb",
    "wb": "wb",
    "tieba": "tieba",
    "zhihu": "zhihu",
    "kuaishou": "ks",
    "ks": "ks",
}

SUPPORTED_CRAWLER_TYPES = {"search", "detail", "creator", "homefeed"}


class MediaCrawlerIntegrationService:
    def __init__(
        self,
        *,
        settings: MediaCrawlerSettings,
        mysql_settings: MySQLSettings,
        redis_settings: RedisSettings,
        logging_settings: LoggingSettings,
        backend_root: Path,
    ) -> None:
        self.settings = settings
        self.mysql_settings = mysql_settings
        self.redis_settings = redis_settings
        self.logging_settings = logging_settings
        self.backend_root = backend_root

        self.sidecar = SignSrvSidecar(settings=settings, logging_settings=logging_settings)
        self.crawler_engine = CrawlerEngineSidecar(settings=settings, backend_root=backend_root)
        self.runner = MediaCrawlerRunner(settings=settings, backend_root=backend_root)

    async def startup(self) -> None:
        if not self.settings.enabled:
            return
        await self.sidecar.ensure_started()
        await self.crawler_engine.ensure_started()

    async def shutdown(self) -> None:
        if not self.settings.enabled:
            return
        import asyncio
        await asyncio.gather(
            self.sidecar.shutdown(),
            self.crawler_engine.shutdown(),
        )

    def status(self) -> dict[str, Any]:
        status = self.sidecar.status()
        status["crawler_engine"] = self.crawler_engine.status()
        status["python_project_dir"] = self.settings.python_project_dir
        status["signsrv_project_dir"] = self.settings.signsrv_project_dir
        return status

    def build_job_spec(self, record: TaskRecord) -> MediaCrawlerJobSpec:
        config = dict(record.config or {})
        platform = self._resolve_platform(config.get("platform") or record.platform)
        crawler_type = self._resolve_crawler_type(config, source_type=record.source_type)

        keywords = None
        urls: list[str] = []
        if crawler_type == "search":
            keywords = self._normalize_keywords(config.get("keywords") or config.get("keyword") or record.source_value)
            if not keywords:
                raise ValueError("Missing keywords for search crawler task")
        elif crawler_type in {"detail", "creator"}:
            urls = self._normalize_urls(config.get("urls") or record.source_value)
            if crawler_type == "detail" and platform == "dy":
                urls = [self._normalize_douyin_detail_url(item) for item in urls]
            if not urls:
                raise ValueError(f"Missing urls/source_value for crawler type={crawler_type}")

        env_overrides = self._base_env_overrides(task_id=record.task_id)
        env_overrides.update(self._extract_env_overrides(config))

        config_overrides = self._base_config_overrides(task_id=record.task_id)
        config_overrides.update(self._extract_config_overrides(config))

        enable_comments = self._get_optional_bool(config, "enable_comments")
        enable_sub_comments = self._get_optional_bool(config, "enable_sub_comments")
        enable_checkpoint = self._get_optional_bool(config, "enable_checkpoint")
        checkpoint_id = self._get_optional_str(config, "checkpoint_id")
        timeout_seconds = int(config.get("timeout_seconds") or self.settings.run_timeout_seconds)

        return MediaCrawlerJobSpec(
            task_id=record.task_id,
            platform=platform,
            crawler_type=crawler_type,
            keywords=keywords,
            urls=urls,
            enable_comments=enable_comments,
            enable_sub_comments=enable_sub_comments,
            enable_checkpoint=enable_checkpoint,
            checkpoint_id=checkpoint_id,
            timeout_seconds=timeout_seconds,
            env_overrides=env_overrides,
            config_overrides=config_overrides,
        )

    def run_job(self, job_spec: MediaCrawlerJobSpec) -> MediaCrawlerRunResult:
        return self.runner.run(job_spec)

    def _base_env_overrides(self, *, task_id: str) -> dict[str, str]:
        sqlite_path = self.backend_root / "runtime" / "mediacrawler" / "sqlite" / f"{task_id}.db"
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)

        return {
            "RELATION_DB_HOST": self.mysql_settings.host,
            "RELATION_DB_PORT": str(self.mysql_settings.port),
            "RELATION_DB_USER": self.mysql_settings.user,
            "RELATION_DB_PWD": self.mysql_settings.password,
            "RELATION_DB_NAME": self.mysql_settings.database,
            "REDIS_DB_HOST": self.redis_settings.host,
            "REDIS_DB_PORT": str(self.redis_settings.port),
            "REDIS_DB_NUM": str(self.redis_settings.db),
            "REDIS_DB_PWD": self.redis_settings.password,
            "SIGN_SRV_HOST": self.settings.signsrv_host,
            "SIGN_SRV_PORT": str(self.settings.signsrv_port),
            "ACCOUNT_POOL_SAVE_TYPE": self.settings.default_account_pool_save_type,
            "COOKIE_BRIDGE_URL": self.settings.default_cookie_bridge_url,
            "DB_TYPE": self.settings.default_db_type,
            "SQLITE_DB_PATH": str(sqlite_path),
        }

    def _base_config_overrides(self, *, task_id: str) -> dict[str, Any]:
        return {
            "SAVE_DATA_OPTION": self.settings.default_save_data_option,
            "ENABLE_IP_PROXY": self.settings.default_enable_ip_proxy,
            "CHECKPOINT_STORAGE_TYPE": self.settings.default_checkpoint_storage_type,
        }

    @staticmethod
    def _extract_env_overrides(config: dict[str, Any]) -> dict[str, str]:
        env: dict[str, str] = {}
        custom_env = config.get("mediacrawler_env")
        if isinstance(custom_env, dict):
            for key, value in custom_env.items():
                if value is None:
                    continue
                env[str(key)] = str(value)

        direct_env_map = {
            "relation_db_host": "RELATION_DB_HOST",
            "relation_db_port": "RELATION_DB_PORT",
            "relation_db_user": "RELATION_DB_USER",
            "relation_db_pwd": "RELATION_DB_PWD",
            "relation_db_name": "RELATION_DB_NAME",
            "redis_db_host": "REDIS_DB_HOST",
            "redis_db_port": "REDIS_DB_PORT",
            "redis_db_num": "REDIS_DB_NUM",
            "redis_db_pwd": "REDIS_DB_PWD",
            "sign_srv_host": "SIGN_SRV_HOST",
            "sign_srv_port": "SIGN_SRV_PORT",
            "account_pool_save_type": "ACCOUNT_POOL_SAVE_TYPE",
            "cookie_bridge_url": "COOKIE_BRIDGE_URL",
            "db_type": "DB_TYPE",
            "sqlite_db_path": "SQLITE_DB_PATH",
            "crawler_cookie_account_id": "CRAWLER_COOKIE_ACCOUNT_ID",
        }
        for source_key, target_key in direct_env_map.items():
            value = config.get(source_key)
            if value is not None:
                env[target_key] = str(value)
        return env

    @staticmethod
    def _extract_config_overrides(config: dict[str, Any]) -> dict[str, Any]:
        overrides: dict[str, Any] = {}
        custom_overrides = config.get("mediacrawler_config_overrides")
        if isinstance(custom_overrides, dict):
            overrides.update(custom_overrides)

        direct_map = {
            "save_data_option": "SAVE_DATA_OPTION",
            "enable_ip_proxy": "ENABLE_IP_PROXY",
            "checkpoint_storage_type": "CHECKPOINT_STORAGE_TYPE",
            "crawler_max_notes_count": "CRAWLER_MAX_NOTES_COUNT",
            "douyin_search_content_type": "DOUYIN_SEARCH_CONTENT_TYPE",
            "content_kind": "DOUYIN_SEARCH_CONTENT_TYPE",
            "max_concurrency_num": "MAX_CONCURRENCY_NUM",
            "crawler_time_sleep": "CRAWLER_TIME_SLEEP",
        }
        for source_key, target_key in direct_map.items():
            if source_key in config:
                overrides[target_key] = config[source_key]
        if "contentKind" in config:
            overrides["DOUYIN_SEARCH_CONTENT_TYPE"] = config["contentKind"]
        if "DOUYIN_SEARCH_CONTENT_TYPE" in overrides:
            overrides["DOUYIN_SEARCH_CONTENT_TYPE"] = MediaCrawlerIntegrationService._normalize_content_type(
                overrides["DOUYIN_SEARCH_CONTENT_TYPE"]
            )
        return overrides

    @staticmethod
    def _normalize_content_type(value: Any) -> str:
        content_type = str(value or "all").strip().lower()
        if content_type in {"photo", "photos", "image", "images", "图文"}:
            return "image"
        if content_type in {"video", "videos", "视频"}:
            return "video"
        return "all"

    @staticmethod
    def _resolve_platform(raw_platform: str | None) -> str:
        key = str(raw_platform or "").strip().lower()
        resolved = PLATFORM_MAP.get(key)
        if not resolved:
            raise ValueError(f"Unsupported platform for MediaCrawler: {raw_platform}")
        return resolved

    @staticmethod
    def _resolve_crawler_type(config: dict[str, Any], *, source_type: str) -> str:
        raw = str(config.get("crawler_type") or "").strip().lower()
        if raw in SUPPORTED_CRAWLER_TYPES:
            return raw
        source_key = str(source_type or "").strip().lower()
        if source_key in {"keyword", "search"}:
            return "search"
        if source_key in {"creator", "author", "account", "user"}:
            return "creator"
        if source_key in {"detail", "link", "url", "note", "post"}:
            return "detail"
        return "search"

    @staticmethod
    def _normalize_keywords(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            text = value.strip()
            return text or None
        if isinstance(value, list):
            parts = [str(item).strip() for item in value if str(item).strip()]
            return ",".join(parts) if parts else None
        return str(value).strip() or None

    @staticmethod
    def _normalize_urls(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            cleaned = value.replace("\r", "\n")
            tokens = []
            for segment in cleaned.split("\n"):
                tokens.extend(segment.split(","))
            return [token.strip() for token in tokens if token.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return [str(value).strip()]

    @staticmethod
    def _normalize_douyin_detail_url(value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        for pattern in (r"/(?:video|note)/(\d{10,30})", r"[?&](?:modal_id|aweme_id|group_id)=(\d{10,30})"):
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        match = re.search(r"(?<!\d)(7\d{15,25})(?!\d)", text)
        return match.group(1) if match else text

    @staticmethod
    def _get_optional_bool(config: dict[str, Any], key: str) -> bool | None:
        if key not in config:
            return None
        value = config.get(key)
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off"}:
            return False
        return None

    @staticmethod
    def _get_optional_str(config: dict[str, Any], key: str) -> str | None:
        if key not in config:
            return None
        value = str(config.get(key) or "").strip()
        return value or None
