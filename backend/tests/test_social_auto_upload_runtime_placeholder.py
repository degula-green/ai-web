from pathlib import Path

import pytest

from app.core.exceptions import ContractError
from app.modules.publishing.infrastructure.runtime.social_auto_upload_runtime import (
    SocialAccountState,
    SocialAutoUploadRuntime,
)


def test_runtime_constructs_and_missing_storage_state_returns_none(tmp_path: Path) -> None:
    runtime = SocialAutoUploadRuntime(backend_root=tmp_path)
    assert runtime.IMPLEMENTED is False
    assert runtime.PUBLISH_IMPLEMENTED is False
    assert runtime.runtime_root == tmp_path / "runtime" / "publishing"
    assert runtime.load_storage_state(account_id=1, platform_code="douyin") is None


def test_runtime_exports_and_loads_storage_state(tmp_path: Path) -> None:
    runtime = SocialAutoUploadRuntime(backend_root=tmp_path)
    path = runtime.export_storage_state(
        account_id=7,
        platform_code="douyin",
        cookies=[{"name": "sessionid", "value": "fresh-token"}],
        local_storage={"origins": [{"origin": "https://www.douyin.com", "localStorage": []}]},
    )
    assert path.is_file()
    payload = runtime.load_storage_state(account_id=7, platform_code="douyin")
    assert payload is not None
    assert payload["accountId"] == 7
    assert payload["platformCode"] == "douyin"
    assert payload["cookies"][0]["name"] == "sessionid"
    assert payload["cookies"][0]["domain"] == ".douyin.com"
    assert payload["localStorage"]["origins"][0]["origin"] == "https://www.douyin.com"


def test_runtime_publish_fails_explicitly(tmp_path: Path) -> None:
    runtime = SocialAutoUploadRuntime(backend_root=tmp_path)
    with pytest.raises(ContractError) as exc_info:
        runtime.publish(platform_type=1, title="test")
    assert exc_info.value.status_code == 501


def test_social_account_state_defaults() -> None:
    account = SocialAccountState(
        account_id=1,
        platform_type=1,
        platform_code="douyin",
        platform_name="抖音",
        account_name="tester",
    )
    assert account.cookies == []
    assert account.local_storage is None
