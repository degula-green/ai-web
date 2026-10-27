# -*- coding: utf-8 -*-
"""
API 路由测试
"""
import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestModesEndpoint:
    def test_modes_returns_list(self, client):
        response = client.get("/api/v1/remix/modes")
        assert response.status_code == 200
        data = response.json()
        assert "modes" in data
        assert len(data["modes"]) >= 4

    def test_modes_have_required_fields(self, client):
        response = client.get("/api/v1/remix/modes")
        data = response.json()

        for mode in data["modes"]:
            assert "value" in mode
            assert "label" in mode
            assert "description" in mode

    def test_modes_include_core_types(self, client):
        response = client.get("/api/v1/remix/modes")
        data = response.json()

        values = [m["value"] for m in data["modes"]]
        assert "summarize" in values
        assert "analyze" in values
        assert any(v in values for v in ("template", "imitate"))
        assert any(v in values for v in ("style_explore", "rewrite"))


class TestAnalyzeEndpoint:
    def test_analyze_empty_url_returns_400(self, client):
        response = client.post(
            "/api/v1/remix/analyze",
            json={"url": ""}
        )
        assert response.status_code == 400


class TestChatEndpoint:
    def test_chat_empty_message_returns_400(self, client):
        response = client.post(
            "/api/v1/remix/chat",
            json={"message": ""}
        )
        assert response.status_code == 400


class TestCopywritingEndpoints:
    def test_extract_empty_url_returns_400(self, client):
        response = client.post(
            "/api/v1/copywriting/extract",
            json={"url": ""}
        )
        assert response.status_code == 400

    def test_rewrite_empty_text_returns_400(self, client):
        response = client.post(
            "/api/v1/copywriting/rewrite",
            json={"text": ""}
        )
        assert response.status_code == 400
