from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.models.platform_account import PlatformAccount, PlatformAccountSession
from app.db.session import build_session_factory
from app.main import create_app


def _login(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "loginType": "username",
            "identity": "superadmin",
            "credential": "123456",
            "deviceType": "web",
            "deviceId": f"pytest-platform-{uuid4().hex}",
            "clientVersion": "pytest",
            "osName": "Windows",
            "browserName": "pytest",
            "ipAddress": "127.0.0.1",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["accessToken"]


def test_platform_accounts_endpoints_with_session_fields() -> None:
    client = TestClient(create_app())
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    account_name = f"acct_{uuid4().hex[:12]}"
    settings = get_settings()
    factory = build_session_factory(settings)

    with factory() as db:
        account = PlatformAccount(
            owner_user_id=1,
            platform_code="douyin",
            account_name=account_name,
            nickname="pytest_account",
            auth_status="authorized",
            is_deleted=False,
        )
        db.add(account)
        db.flush()

        session = PlatformAccountSession(
            account_id=account.id,
            cookies=[{"name": "LOGIN_STATUS", "value": "1"}],
            local_storage={"HasUserLogin": "1"},
            auth_type="cookie",
            cookie_blob="{\"demo\":true}",
            status="active",
            expires_at=datetime.now(),
            last_sync_at=datetime.now(),
            last_validated_at=datetime.now(),
            last_refresh_at=datetime.now(),
            cookie_version=1,
        )
        db.add(session)
        db.commit()

    list_resp = client.get("/api/v1/platforms/accounts?platformCode=douyin", headers=headers)
    assert list_resp.status_code == 200, list_resp.text
    payload = list_resp.json()["data"]
    rows = payload["list"]
    target = next((item for item in rows if item["accountName"] == account_name), None)
    assert target is not None
    assert target["authType"] == "cookie"
    assert target["sessionStatus"] == "active"
    assert "lastValidatedAt" in target
    assert "lastRefreshAt" in target

    unbind_resp = client.delete(f"/api/v1/platforms/accounts/{target['accountId']}", headers=headers)
    assert unbind_resp.status_code == 200, unbind_resp.text

    with factory() as db:
        updated = db.query(PlatformAccountSession).filter(PlatformAccountSession.account_id == target["accountId"]).first()
        assert updated is not None
        assert updated.status == "revoked"
