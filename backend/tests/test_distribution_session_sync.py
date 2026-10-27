from __future__ import annotations

from pathlib import Path
from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

from app.core.config import get_settings
from app.db.models.platform_account import PlatformAccount, PlatformAccountSession
from app.db.models.publish_plan import PublishPlanItemModel
from app.db.repositories.publish_plan_repository import PublishPlanItemRecord, PublishPlanRepository
from app.db.session import build_session_factory
from app.modules.publishing.infrastructure.runtime.social_auto_upload_runtime import SocialAutoUploadRuntime
from app.services.distribution_service import DistributionService


def _build_distribution_service(*, session_factory, publisher_runtime: SocialAutoUploadRuntime) -> DistributionService:
    return DistributionService(
        channel_plugin=SimpleNamespace(send_alert=lambda *_args, **_kwargs: None),
        session_factory=session_factory,
        content_repository=None,
        platform_account_content_repository=None,
        creation_draft_repository=None,
        publish_plan_repository=None,
        publisher_runtime=publisher_runtime,
    )


def test_social_auto_upload_runtime_load_storage_state(tmp_path: Path) -> None:
    backend_root = tmp_path / "backend"
    backend_root.mkdir(parents=True, exist_ok=True)
    runtime = SocialAutoUploadRuntime(backend_root=backend_root)

    runtime.export_storage_state(
        account_id=7,
        platform_code="douyin",
        cookies=[{"name": "sessionid", "value": "fresh-token"}],
        local_storage={
            "origins": [
                {
                    "origin": "https://www.douyin.com",
                    "localStorage": [{"name": "HasUserLogin", "value": "1"}],
                }
            ]
        },
    )

    payload = runtime.load_storage_state(account_id=7, platform_code="douyin")

    assert payload is not None
    assert payload["accountId"] == 7
    assert payload["platformCode"] == "douyin"
    cookies = payload["cookies"]
    assert isinstance(cookies, list)
    assert cookies[0]["name"] == "sessionid"
    assert cookies[0]["domain"] == ".douyin.com"
    local_storage = payload["localStorage"]
    assert isinstance(local_storage, dict)
    assert local_storage["origins"][0]["origin"] == "https://www.douyin.com"
    assert local_storage["origins"][0]["localStorage"][0]["name"] == "HasUserLogin"


def test_distribution_service_syncs_runtime_session_state(tmp_path: Path) -> None:
    settings = get_settings()
    session_factory = build_session_factory(settings)

    account_name = f"runtime_sync_{uuid4().hex[:12]}"
    with session_factory() as db:
        account = PlatformAccount(
            owner_user_id=1,
            platform_code="douyin",
            account_name=account_name,
            nickname="runtime_sync",
            auth_status="authorized",
            account_status="active",
            is_deleted=False,
        )
        db.add(account)
        db.flush()

        session_row = PlatformAccountSession(
            account_id=account.id,
            cookies=[{"name": "sessionid", "value": "stale-token"}],
            local_storage={"origins": [{"origin": "https://www.douyin.com", "localStorage": []}]},
            status="active",
            session_status="active",
            cookie_version=3,
        )
        db.add(session_row)
        db.commit()
        account_id = int(account.id)

    backend_root = tmp_path / "backend"
    backend_root.mkdir(parents=True, exist_ok=True)
    runtime = SocialAutoUploadRuntime(backend_root=backend_root)
    runtime.export_storage_state(
        account_id=account_id,
        platform_code="douyin",
        cookies=[{"name": "sessionid", "value": "fresh-token", "expires": 4102444800}],
        local_storage={
            "origins": [
                {
                    "origin": "https://www.douyin.com",
                    "localStorage": [{"name": "HasUserLogin", "value": "1"}],
                }
            ]
        },
    )

    service = _build_distribution_service(session_factory=session_factory, publisher_runtime=runtime)
    service._sync_runtime_session_state(account_id=account_id, platform_code="douyin")

    with session_factory() as db:
        refreshed = db.query(PlatformAccountSession).filter(PlatformAccountSession.account_id == account_id).first()
        assert refreshed is not None
        assert refreshed.cookies[0]["value"] == "fresh-token"
        assert refreshed.local_storage["origins"][0]["localStorage"][0]["name"] == "HasUserLogin"
        assert refreshed.cookie_version == 4
        assert refreshed.cookie_hash
        assert refreshed.storage_hash
        assert refreshed.last_sync_at is not None
        assert refreshed.last_refresh_at is not None
        assert refreshed.expires_at is not None
        assert refreshed.source_type == "upload_runtime"


def test_publish_plan_repository_serializes_datetime_json_fields() -> None:
    settings = get_settings()
    session_factory = build_session_factory(settings)
    repository = PublishPlanRepository(session_factory)

    request_group_id = f"pubplan_test_{uuid4().hex[:12]}"
    publish_datetime = datetime(2026, 5, 17, 16, 39)

    created = repository.create_item(
        PublishPlanItemRecord(
            request_group_id=request_group_id,
            owner_user_id=1,
            draft_id=f"draft_{uuid4().hex[:16]}",
            task_ref=f"draft_{uuid4().hex[:16]}",
            platform_type=3,
            platform_code="douyin",
            platform_name="抖音",
            account_id=18,
            account_name="夜喵子",
            title="datetime json serialize",
            video_url="http://example.com/video.mp4",
            topics=[],
            publish_mode="headed",
            publish_time_type="schedule",
            scheduled_at=publish_datetime.isoformat(),
            submitted_at=publish_datetime.isoformat(),
            status="scheduled",
            status_message="publish submitted",
            downstream_status_code=200,
            downstream_payload={
                "enableTimer": True,
                "publishDatetime": publish_datetime,
                "dailyTimes": [publish_datetime.hour],
            },
            downstream_response={"scheduledAt": publish_datetime},
            extra_data={"nested": {"publishedAt": publish_datetime}},
        )
    )

    assert created.id is not None
    assert created.downstream_payload is not None
    assert created.downstream_payload["publishDatetime"] == publish_datetime.isoformat()
    assert created.downstream_response is not None
    assert created.downstream_response["scheduledAt"] == publish_datetime.isoformat()
    assert created.extra_data is not None
    assert created.extra_data["nested"]["publishedAt"] == publish_datetime.isoformat()

    with session_factory() as db:
        db.query(PublishPlanItemModel).filter(PublishPlanItemModel.id == created.id).delete()
        db.commit()
