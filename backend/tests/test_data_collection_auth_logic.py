from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from app.core.config import RedisSettings
from app.core.exceptions import ContractError
from app.services.data_collection_service import DataCollectionService


class FakeRedis:
    def __init__(self) -> None:
        self.kv: dict[str, str] = {}

    def set(self, key: str, value: str, nx: bool = False, ex: int | None = None):
        if nx and key in self.kv:
            return False
        self.kv[key] = value
        return True

    def eval(self, script: str, numkeys: int, key: str, token: str):
        if self.kv.get(key) == token:
            del self.kv[key]
            return 1
        return 0

    def setex(self, key: str, ttl: int, value: str):
        self.kv[key] = value


@dataclass
class FakeTask:
    id: int
    task_no: str
    content_kind: str
    keyword: str | None = None
    task_status: str = "running"
    total_count: int = 0
    pending_count: int = 0
    imported_count: int = 0
    created_at: object | None = None
    updated_at: object | None = None
    auth_account_id: int | None = None


class FakeRepository:
    def __init__(self, account, session):
        self.account = account
        self.session = session
        self.validated_called = False

    def get_platform_auth_bundle(self, **kwargs):
        return self.account, self.session

    def mark_platform_auth_need_reauth(self, **kwargs):
        self.account.auth_status = "need_reauth"

    def create_crawl_task(self, **kwargs):
        return FakeTask(id=1, task_no=kwargs["task_no"], content_kind=kwargs["content_kind"], auth_account_id=kwargs.get("auth_account_id"))

    def update_crawl_task(self, **kwargs):
        return None

    def mark_platform_auth_validated(self, **kwargs):
        self.validated_called = True


class FakeCrawlerService:
    def __init__(self):
        self.last_call = None

    def crawl_keyword(self, **kwargs):
        self.last_call = kwargs
        return [{"content_id": "123", "title": "x", "desc": "d", "author_name": "a", "author_id": "u"}]


class FakeImportService:
    def normalize_crawl_item(self, **kwargs):
        return {
            "contentId": "123",
            "contentKind": "image",
            "title": "x",
            "summary": "d",
        }


class FakeExportService:
    pass


def _build_service(account_status: str, session_status: str, expires_at=None):
    account = SimpleNamespace(id=101, auth_status=account_status)
    session = SimpleNamespace(
        status=session_status,
        expires_at=expires_at,
        cookie_blob='[{"name":"sid_guard","value":"abc"},{"name":"LOGIN_STATUS","value":"1"}]',
        cookies=None,
    )
    repo = FakeRepository(account, session)
    crawler = FakeCrawlerService()
    service = DataCollectionService(
        repository=repo,
        crawler_service=crawler,
        import_service=FakeImportService(),
        export_service=FakeExportService(),
        redis_settings=RedisSettings(host="127.0.0.1", port=6379, db=15, username="", password="", use_ssl=False),
    )
    service.redis = FakeRedis()
    return service, repo, crawler


def test_keyword_task_requires_valid_auth_session() -> None:
    service, _, _ = _build_service(account_status="authorized", session_status="need_reauth")
    with pytest.raises(ContractError) as exc:
        service.create_keyword_task(
            owner_user_id=1,
            platform_code="douyin",
            auth_account_id=101,
            keyword="测试",
            content_kind="image",
            time_range="24h",
            sort_by="heat",
            page_size=20,
        )
    assert exc.value.status_code == 409


def test_keyword_task_uses_db_cookie_auth() -> None:
    service, repo, crawler = _build_service(account_status="authorized", session_status="active")
    result = service.create_keyword_task(
        owner_user_id=1,
        platform_code="douyin",
        auth_account_id=101,
        keyword="测试",
        content_kind="image",
        time_range="24h",
        sort_by="heat",
        page_size=20,
    )

    assert result["authAccountId"] == 101
    assert crawler.last_call is not None
    assert crawler.last_call["use_cookie_auth"] is True
    assert "sid_guard=abc" in crawler.last_call["cookie_str"]
    assert repo.validated_called is True
