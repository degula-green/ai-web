from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.core.config import get_settings
from app.core.exceptions import ContractError
from app.db.models.platform_account import (
    CrawlerCookieAccountBinding,
    PlatformAccount,
    PlatformAccountSession,
    PlatformCookieBridgeBinding,
)
from app.db.session import build_session_factory
from app.services.platform_account_service import PlatformAccountService


def test_parse_bilibili_nav_payload_returns_verified_identity() -> None:
    snapshot = PlatformAccountService._parse_bilibili_nav_payload(
        {
            "code": 0,
            "message": "0",
            "data": {
                "isLogin": True,
                "mid": 409557909,
                "uname": "德古拉绿老师",
                "face": "//i0.hdslb.com/bfs/face/avatar.jpg",
            },
        }
    )

    assert snapshot["platform_uid"] == "409557909"
    assert snapshot["uid"] == "409557909"
    assert snapshot["nickname"] == "德古拉绿老师"
    assert snapshot["avatar_url"] == "https://i0.hdslb.com/bfs/face/avatar.jpg"
    assert snapshot["account_name"] == "德古拉绿老师"


def test_parse_bilibili_nav_payload_rejects_logged_out_session() -> None:
    with pytest.raises(ContractError) as exc:
        PlatformAccountService._parse_bilibili_nav_payload(
            {"code": -101, "message": "账号未登录", "data": {"isLogin": False}}
        )

    assert exc.value.status_code == 400
    assert "B站登录态已失效" in exc.value.message


def test_bind_bilibili_refreshes_identity_and_marks_account_active(monkeypatch) -> None:
    factory = build_session_factory(get_settings())
    owner_id = 900000 + int(uuid4().hex[:6], 16) % 90000
    service = PlatformAccountService()
    db = factory()
    account = PlatformAccount(
        owner_user_id=owner_id,
        platform_code="bilibili",
        account_name="德古拉绿老师",
        nickname="德古拉绿老师",
        auth_status="authorized",
        account_status="needs_rebind",
        account_type="cookie_bridge",
        is_deleted=False,
    )
    db.add(account)
    db.commit()

    async def fake_bridge_get(bridge_url, path, params=None):
        if path == "/api/accounts":
            return {
                "accounts": [
                    {
                        "client_id": "client-1",
                        "connected": True,
                        "nicknames": {"bili": "德古拉绿老师"},
                        "platforms": {"bili": {"has_cookies": True}},
                    }
                ]
            }
        if path == "/api/cookies/bili":
            return {"cookies": "SESSDATA=abc; bili_jct=def; DedeUserID=409557909"}
        raise AssertionError(path)

    async def fake_bilibili_profile(*, cookies):
        return {
            "platform_uid": "409557909",
            "uid": "409557909",
            "user_id": "409557909",
            "nickname": "德古拉绿老师",
            "avatar_url": "https://i0.hdslb.com/bfs/face/avatar.jpg",
            "account_name": "德古拉绿老师",
        }

    monkeypatch.setattr(service, "_bridge_get", fake_bridge_get)
    monkeypatch.setattr(service, "_fetch_bilibili_self_profile", fake_bilibili_profile)

    try:
        result = asyncio.run(
            service.bind_cookie_bridge_client(
                db,
                owner_id=owner_id,
                bridge_url="http://127.0.0.1:8274",
                platform_code="bilibili",
                client_id="client-1",
            )
        )

        assert result["accountId"] == account.id

        db.expire_all()
        refreshed = db.query(PlatformAccount).filter(PlatformAccount.id == account.id).one()
        assert refreshed.platform_uid == "409557909"
        assert refreshed.identity_type == "platform_uid"
        assert refreshed.identity_value == "409557909"
        assert refreshed.nickname == "德古拉绿老师"
        assert refreshed.avatar_url == "https://i0.hdslb.com/bfs/face/avatar.jpg"
        assert refreshed.auth_status == "authorized"
        assert refreshed.account_status == "active"
        assert refreshed.last_identity_verified_at is not None
        assert refreshed.last_identity_error is None
    finally:
        db.rollback()
        account_ids = [row[0] for row in db.query(PlatformAccount.id).filter(PlatformAccount.owner_user_id == owner_id).all()]
        if account_ids:
            db.query(PlatformAccountSession).filter(PlatformAccountSession.account_id.in_(account_ids)).delete(synchronize_session=False)
            db.query(PlatformCookieBridgeBinding).filter(PlatformCookieBridgeBinding.platform_account_id.in_(account_ids)).delete(synchronize_session=False)
            db.query(CrawlerCookieAccountBinding).filter(CrawlerCookieAccountBinding.platform_account_id.in_(account_ids)).delete(synchronize_session=False)
        db.query(PlatformAccount).filter(PlatformAccount.owner_user_id == owner_id).delete(synchronize_session=False)
        db.commit()
        db.close()


def test_bind_bilibili_rejects_invalid_login_state(monkeypatch) -> None:
    factory = build_session_factory(get_settings())
    db = factory()
    service = PlatformAccountService()

    async def fake_bridge_get(bridge_url, path, params=None):
        if path == "/api/accounts":
            return {
                "accounts": [
                    {
                        "client_id": "client-1",
                        "connected": True,
                        "nicknames": {"bili": "德古拉绿老师"},
                        "platforms": {"bili": {"has_cookies": True}},
                    }
                ]
            }
        if path == "/api/cookies/bili":
            return {"cookies": "SESSDATA=expired; DedeUserID=409557909"}
        raise AssertionError(path)

    async def fake_bilibili_profile(*, cookies):
        raise ContractError("B站登录态已失效，请重新登录后再绑定：账号未登录", status_code=400)

    monkeypatch.setattr(service, "_bridge_get", fake_bridge_get)
    monkeypatch.setattr(service, "_fetch_bilibili_self_profile", fake_bilibili_profile)

    try:
        with pytest.raises(ContractError) as exc:
            asyncio.run(
                service.bind_cookie_bridge_client(
                    db,
                    owner_id=900001,
                    bridge_url="http://127.0.0.1:8274",
                    platform_code="bilibili",
                    client_id="client-1",
                )
            )

        assert exc.value.status_code == 400
        assert db.query(PlatformAccount).filter(PlatformAccount.owner_user_id == 900001).count() == 0
    finally:
        db.rollback()
        db.close()
