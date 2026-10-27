import redis
import httpx
from typing import Any, Protocol

from sqlalchemy import bindparam, text

from app.core.exceptions import ContractError
from app.core.config import RedisSettings
from app.core.logging import get_logger
from app.core.task_state_machine import TaskState, can_transition
from app.db.repositories.task_repository import TaskRecord, TaskRepository
from app.services.memory_service import MemoryService
from app.utils.time import utc_now_iso

from .models import MediaCrawlerJobSpec
from .service import MediaCrawlerIntegrationService

logger = get_logger(__name__)


def _pick_api_error(api_task: dict[str, Any]) -> str:
    summary = api_task.get("summary")
    if isinstance(summary, dict):
        summary_error = summary.get("error")
        if summary_error:
            return str(summary_error)
    error = api_task.get("error")
    if error:
        return str(error)
    return "MediaCrawler task failed"


def _to_user_friendly_error(raw_error: str) -> str:
    normalized = (raw_error or "").strip()
    lowered = normalized.lower()

    if "用户未登录" in normalized or "登录检测失败" in normalized:
        return "采集失败：登录状态已失效，请重新授权或更新 Cookie。"
    if "cookie" in lowered and ("过期" in normalized or "失效" in normalized or "invalid" in lowered):
        return "采集失败：Cookie 已失效，请重新授权或更新 Cookie。"
    if "账号池中没有可用的账号" in normalized:
        return "采集失败：服务器账号池已耗尽，暂时没有可用采集账号。"
    if "account blocked" in lowered or "blocked" in lowered:
        return "采集失败：当前采集账号或代理已被平台风控，请稍后重试或更换账号。"
    if "request params incrr" in lowered or "params incrr" in lowered:
        return "采集失败：平台接口请求参数异常，可能是签名、版本或风控校验导致。"
    if "process exited with code" in lowered:
        return "采集失败：爬虫进程异常退出，请查看后端日志。"
    return normalized or "采集失败：爬虫执行异常。"


class TaskStartExecutor(Protocol):
    def validate_before_submit(self, record: TaskRecord) -> None:
        ...

    def submit(self, record: TaskRecord) -> bool:
        ...


class MediaCrawlerTaskOrchestrator:
    def __init__(
        self,
        *,
        task_repository: TaskRepository,
        memory_service: MemoryService,
        crawler_service: MediaCrawlerIntegrationService,
        redis_settings: RedisSettings,
        enabled: bool,
    ) -> None:
        self.task_repository = task_repository
        self.memory_service = memory_service
        self.crawler_service = crawler_service
        self.redis_settings = redis_settings
        self.enabled = enabled
        self._redis_client = redis.Redis.from_url(redis_settings.url, decode_responses=True)
        self._queue_name = "mediacrawler:task_queue"

    def validate_before_submit(self, record: TaskRecord) -> None:
        if not self.enabled or not self._is_mediacrawler_task(record):
            return
        account = self._resolve_crawler_cookie_account(record)
        config = dict(record.config or {})
        config.update(account)
        record.config = config

    def submit(self, record: TaskRecord) -> bool:
        if not self.enabled:
            return False
        if not self._is_mediacrawler_task(record):
            return False

        try:
            account = self._resolve_crawler_cookie_account(record)
            job_spec = self.crawler_service.build_job_spec(record)
            payload = self._build_api_payload(job_spec, backend_task_id=record.task_id)
            payload["crawler_cookie_account_id"] = account["crawler_cookie_account_id"]
            config = dict(record.config or {})
            config.update(account)
            if job_spec.env_overrides:
                payload["env_overrides"] = job_spec.env_overrides
            if job_spec.config_overrides:
                payload["config_overrides"] = job_spec.config_overrides
            if config.get("crawler_max_notes_count") is not None:
                payload["crawler_max_notes_count"] = int(config["crawler_max_notes_count"])
            api_base_url = self.crawler_service.settings.crawler_api_base_url.rstrip("/")

            with httpx.Client(timeout=15.0, trust_env=False) as client:
                response = client.post(f"{api_base_url}/crawl", json=payload)
                response.raise_for_status()
                api_task = response.json()

            config.update(
                {
                    "collector": "mediacrawler",
                    "mediacrawler_api_base_url": api_base_url,
                    "mediacrawler_api_task_id": api_task.get("task_id"),
                    "checkpoint_id": api_task.get("checkpoint_id") or payload.get("checkpoint_id"),
                    "checkpoint_key": api_task.get("checkpoint_key"),
                    "crawler_cookie_account_id": account["crawler_cookie_account_id"],
                    "crawler_cookie_binding_id": account["crawler_cookie_binding_id"],
                    "platform_account_id": account.get("platform_account_id"),
                }
            )
            record.config = config
            if can_transition(record.state, TaskState.COLLECTING):
                record.state = TaskState.COLLECTING
            record.updated_at = utc_now_iso()
            self.task_repository.update(record)

            self.memory_service.record_event(
                task_id=record.task_id,
                snapshot_type="mediacrawler_api_submitted",
                summary=f"Submitted to MediaCrawler API: {api_task.get('task_id')}",
            )
            return True
        except Exception as exc:
            logger.exception("Failed to submit task to MediaCrawler API task_id=%s", record.task_id)
            self._fail(record.task_id, f"MediaCrawler API submit failed: {str(exc)}")
            return False

    def status(self) -> dict[str, object]:
        try:
            queue_len = self._redis_client.llen(self._queue_name)
        except Exception:
            queue_len = -1

        return {
            "enabled": self.enabled,
            "crawler_api_base_url": self.crawler_service.settings.crawler_api_base_url,
            "legacy_queue_name": self._queue_name,
            "legacy_pending_tasks_in_queue": queue_len,
        }

    def sync_task_status(self, record: TaskRecord) -> TaskRecord:
        config = dict(record.config or {})
        api_task_id = str(config.get("mediacrawler_api_task_id") or "").strip()
        api_base_url = str(
            config.get("mediacrawler_api_base_url")
            or self.crawler_service.settings.crawler_api_base_url
        ).rstrip("/")
        if not api_task_id or not api_base_url:
            return record

        try:
            with httpx.Client(timeout=8.0, trust_env=False) as client:
                response = client.get(f"{api_base_url}/task/{api_task_id}")
                response.raise_for_status()
                api_task = response.json()
        except Exception as exc:
            logger.warning(
                "Failed to sync MediaCrawler API task status task_id=%s api_task_id=%s error=%s",
                record.task_id,
                api_task_id,
                exc,
            )
            return record

        api_status = str(api_task.get("status") or "").lower()
        raw_error = _pick_api_error(api_task)
        friendly_error = _to_user_friendly_error(raw_error)
        config.update(
            {
                "mediacrawler_api_status": api_status,
                "mediacrawler_api_finish_time": api_task.get("finish_time"),
                "mediacrawler_api_error": api_task.get("error"),
                "mediacrawler_api_summary": api_task.get("summary"),
                "mediacrawler_api_raw_error": raw_error,
                "mediacrawler_api_friendly_error": friendly_error,
                "checkpoint_id": api_task.get("checkpoint_id") or config.get("checkpoint_id"),
                "checkpoint_key": api_task.get("checkpoint_key") or config.get("checkpoint_key"),
            }
        )
        record.config = config
        if api_status == "failed" and can_transition(record.state, TaskState.FAILED):
            record.state = TaskState.FAILED
            record.error_message = friendly_error[:512]
        elif api_status == "failed":
            record.error_message = friendly_error[:512]
        elif api_status == "completed" and can_transition(record.state, TaskState.MANUAL_INTERVENTION):
            record.state = TaskState.MANUAL_INTERVENTION
            record.error_message = None
        elif api_status in {"pending", "running"} and can_transition(record.state, TaskState.COLLECTING):
            record.state = TaskState.COLLECTING
        record.updated_at = utc_now_iso()
        return self.task_repository.update(record)

    def _fail(self, task_id: str, error_message: str) -> None:
        record = self.task_repository.get(task_id)
        if not record:
            return
        if can_transition(record.state, TaskState.FAILED) and record.state != TaskState.FAILED:
            previous = record.state
            record.state = TaskState.FAILED
            record.updated_at = utc_now_iso()
            record.error_message = error_message[:512]
            self.task_repository.update(record)
            self.memory_service.record_event(
                task_id=task_id,
                snapshot_type="state_transition",
                summary=f"{previous} -> {TaskState.FAILED}",
            )
        else:
            record.error_message = error_message[:512]
            record.updated_at = utc_now_iso()
            self.task_repository.update(record)
        self.memory_service.record_event(
            task_id=task_id,
            snapshot_type="mediacrawler_error",
            summary=error_message[:200],
        )

    def _resolve_crawler_cookie_account(self, record: TaskRecord) -> dict[str, Any]:
        config = dict(record.config or {})
        try:
            crawler_platform = self.crawler_service._resolve_platform(config.get("platform") or record.platform)
        except ValueError as exc:
            raise ContractError(str(exc), status_code=400) from exc

        platform_aliases = self._platform_binding_aliases(crawler_platform, record.platform)
        explicit_account_id = self._coerce_optional_int(
            config.get("crawler_cookie_account_id") or config.get("crawlerCookieAccountId")
        )

        explicit_filter = ""
        params: dict[str, Any] = {
            "user_id": int(record.user_id),
            "platform_codes": platform_aliases,
            "crawler_platform": crawler_platform,
            "cookie_status": 0,
            "active_status": "active",
        }
        if explicit_account_id is not None:
            explicit_filter = " AND b.crawler_cookie_account_id = :explicit_account_id"
            params["explicit_account_id"] = explicit_account_id

        stmt = text(
            f"""
            SELECT
                b.id AS crawler_cookie_binding_id,
                b.platform_account_id AS platform_account_id,
                b.crawler_cookie_account_id AS crawler_cookie_account_id,
                c.account_name AS crawler_cookie_account_name,
                c.platform_name AS crawler_cookie_platform_name
            FROM crawler_cookie_account_bindings b
            INNER JOIN crawler_cookies_account c
                ON c.id = b.crawler_cookie_account_id
            LEFT JOIN platform_accounts pa
                ON pa.id = b.platform_account_id
            WHERE b.owner_user_id = :user_id
              AND b.platform_code IN :platform_codes
              AND b.status = :active_status
              AND c.platform_name = :crawler_platform
              AND c.status = :cookie_status
              AND (
                    b.platform_account_id IS NULL
                    OR (
                        pa.id IS NOT NULL
                        AND pa.owner_user_id = :user_id
                        AND pa.is_deleted = 0
                        AND pa.auth_status IN ('authorized', 'active', 'valid')
                    )
                  )
              {explicit_filter}
            ORDER BY b.is_default DESC, b.priority ASC, b.updated_at DESC, b.id ASC
            LIMIT 1
            """
        ).bindparams(bindparam("platform_codes", expanding=True))

        with self.task_repository.session_scope() as session:
            row = session.execute(stmt, params).mappings().first()

        if not row:
            platform_name = self._display_platform_name(crawler_platform)
            if explicit_account_id is not None:
                raise ContractError(
                    f"当前账号无权使用指定的{platform_name}采集 Cookie，或该 Cookie 已失效。请前往平台授权中心重新授权。",
                    status_code=400,
                )
            raise ContractError(
                f"当前账号没有可用的{platform_name}采集 Cookie，请先前往平台授权中心完成授权。",
                status_code=400,
            )

        return {
            "crawler_cookie_binding_id": int(row["crawler_cookie_binding_id"]),
            "platform_account_id": int(row["platform_account_id"]) if row["platform_account_id"] is not None else None,
            "crawler_cookie_account_id": int(row["crawler_cookie_account_id"]),
            "crawler_cookie_account_name": row["crawler_cookie_account_name"],
            "crawler_cookie_platform_name": row["crawler_cookie_platform_name"],
        }

    @staticmethod
    def _build_api_payload(job_spec: MediaCrawlerJobSpec, *, backend_task_id: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "platform": job_spec.platform,
            "type": job_spec.crawler_type,
            "backend_task_id": backend_task_id,
            "enable_checkpoint": False,
            "enable_comments": job_spec.enable_comments if job_spec.enable_comments is not None else False,
            "enable_sub_comments": job_spec.enable_sub_comments
            if job_spec.enable_sub_comments is not None
            else False,
        }
        if job_spec.keywords:
            payload["keywords"] = job_spec.keywords
        if job_spec.urls:
            payload["urls"] = ",".join(job_spec.urls)
        if job_spec.checkpoint_id:
            payload["checkpoint_id"] = job_spec.checkpoint_id
        return payload

    @staticmethod
    def _is_mediacrawler_task(record: TaskRecord) -> bool:
        config = dict(record.config or {})
        collector = str(config.get("collector") or "").strip().lower()
        return collector == "mediacrawler" or record.task_type in {
            "mediacrawler_collect",
            "crawler_collect",
        }

    @staticmethod
    def _platform_binding_aliases(crawler_platform: str, raw_platform: str | None) -> list[str]:
        aliases = {
            "dy": ["douyin", "dy"],
            "xhs": ["xiaohongshu", "xhs"],
            "bili": ["bilibili", "bili"],
            "wb": ["weibo", "wb"],
            "ks": ["kuaishou", "ks"],
        }.get(crawler_platform, [crawler_platform])
        raw = str(raw_platform or "").strip().lower()
        if raw and raw not in aliases:
            aliases.append(raw)
        return aliases

    @staticmethod
    def _display_platform_name(crawler_platform: str) -> str:
        return {
            "dy": "抖音",
            "xhs": "小红书",
            "bili": "B站",
            "wb": "微博",
            "ks": "快手",
        }.get(crawler_platform, crawler_platform)

    @staticmethod
    def _coerce_optional_int(value: Any) -> int | None:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise ContractError("crawler_cookie_account_id 必须是数字", status_code=400) from exc
