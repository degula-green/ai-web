from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import create_app


def _login(client: TestClient, *, login_type: str, identity: str, credential: str, device_id: str) -> dict:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "loginType": login_type,
            "identity": identity,
            "credential": credential,
            "deviceType": "web",
            "deviceId": device_id,
            "clientVersion": "pytest",
            "osName": "Windows",
            "browserName": "pytest",
            "ipAddress": "127.0.0.1",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_health_and_auth_flow() -> None:
    client = TestClient(create_app())

    health = client.get("/api/v1/health")
    assert health.status_code == 200

    login_data = _login(client, login_type="username", identity="superadmin", credential="123456", device_id=f"pytest-admin-{uuid.uuid4().hex}")
    access_token = login_data["accessToken"]
    refresh_token = login_data["refreshToken"]
    session_id = login_data["sessionId"]
    headers = {"Authorization": f"Bearer {access_token}"}

    wrong_password = client.post(
        "/api/v1/auth/login",
        json={
            "loginType": "username",
            "identity": "superadmin",
            "credential": "bad-password",
            "deviceType": "web",
        },
    )
    assert wrong_password.status_code == 401

    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["data"]["user"]["username"] == "superadmin"

    update_me_with_empty_username = client.patch(
        "/api/v1/auth/me",
        headers=headers,
        json={"username": "", "avatarUrl": "http://example.com/avatar.png"},
    )
    assert update_me_with_empty_username.status_code == 200
    assert update_me_with_empty_username.json()["data"]["avatarUrl"] == "http://example.com/avatar.png"

    me_after_update = client.get("/api/v1/auth/me", headers=headers)
    assert me_after_update.status_code == 200
    assert me_after_update.json()["data"]["user"]["username"] is None

    refreshed = client.post("/api/v1/auth/refresh", json={"refreshToken": refresh_token, "sessionId": session_id})
    assert refreshed.status_code == 200
    new_access_token = refreshed.json()["data"]["accessToken"]
    new_headers = {"Authorization": f"Bearer {new_access_token}"}

    operator_login = _login(client, login_type="phone", identity="13800000002", credential="123456", device_id=f"pytest-operator-{uuid.uuid4().hex}")
    operator_headers = {"Authorization": f"Bearer {operator_login['accessToken']}"}

    forbidden_users = client.get("/api/v1/iam/users", headers=operator_headers)
    assert forbidden_users.status_code == 403

    forbidden_roles = client.get("/api/v1/iam/roles", headers=operator_headers)
    assert forbidden_roles.status_code == 403

    users = client.get("/api/v1/iam/users?pageNo=1&pageSize=20", headers=new_headers)
    assert users.status_code == 200
    assert users.json()["data"]["total"] >= 3

    roles = client.get("/api/v1/iam/roles?pageNo=1&pageSize=20", headers=new_headers)
    assert roles.status_code == 200
    assert roles.json()["data"]["total"] >= 4

    permissions = client.get("/api/v1/iam/permissions?pageNo=1&pageSize=20", headers=new_headers)
    assert permissions.status_code == 200
    assert permissions.json()["data"]["total"] >= 4

    assign_user_roles = client.put(
        "/api/v1/iam/users/3/roles",
        headers=new_headers,
        json={"roleIds": [3, 4], "remark": "pytest"},
    )
    assert assign_user_roles.status_code == 200
    assert assign_user_roles.json()["data"]["roleIds"] == [3, 4]

    assign_role_permissions = client.put(
        "/api/v1/iam/roles/2/permissions",
        headers=new_headers,
        json={"permissionIds": [2, 3], "remark": "pytest"},
    )
    assert assign_role_permissions.status_code == 200
    assert assign_role_permissions.json()["data"]["permissionIds"] == [2, 3]

    sessions = client.get("/api/v1/iam/sessions?pageNo=1&pageSize=20", headers=new_headers)
    assert sessions.status_code == 200
    assert sessions.json()["data"]["total"] >= 2

    force_logout = client.post(
        "/api/v1/iam/sessions/force-logout",
        headers=new_headers,
        json={"sessionId": operator_login["sessionId"], "revokeReason": "pytest force logout"},
    )
    assert force_logout.status_code == 200
    assert force_logout.json()["data"]["sessionStatus"] == "revoked"

    revoked_me = client.get("/api/v1/auth/me", headers=operator_headers)
    assert revoked_me.status_code == 401

    email_target = f"pytest_{uuid.uuid4().hex[:8]}@example.com"
    send_email = client.post("/api/v1/auth/email/send-code", json={"email": email_target, "scene": "register"})
    assert send_email.status_code == 200
    email_code = send_email.json()["data"]["debugCode"]
    verify_email = client.post("/api/v1/auth/email/verify-code", json={"email": email_target, "code": email_code, "scene": "register"})
    assert verify_email.status_code == 200

    phone_target = f"139{uuid.uuid4().int % 10**8:08d}"
    send_sms = client.post("/api/v1/auth/sms/send-code", json={"phone": phone_target, "scene": "register"})
    assert send_sms.status_code == 200
    sms_code = send_sms.json()["data"]["debugCode"]
    verify_sms = client.post("/api/v1/auth/sms/verify-code", json={"phone": phone_target, "code": sms_code, "scene": "register"})
    assert verify_sms.status_code == 200

    logout = client.post("/api/v1/auth/logout", headers=new_headers, json={"sessionId": session_id})
    assert logout.status_code == 200

    after_logout = client.get("/api/v1/auth/me", headers=new_headers)
    assert after_logout.status_code == 401
