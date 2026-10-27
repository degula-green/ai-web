# -*- coding: utf-8 -*-
import asyncio

import httpx

from services.runninghub_workflow import upload_binary_from_url


def test_upload_binary_from_url_retries_retryable_gateway_errors(monkeypatch):
    calls = {"get": 0, "post": 0}

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url):
            calls["get"] += 1
            return httpx.Response(
                200,
                request=httpx.Request("GET", url),
                content=b"fake-image-bytes",
                headers={"content-type": "image/png"},
            )

        async def post(self, url, headers=None, files=None):
            calls["post"] += 1
            if calls["post"] == 1:
                return httpx.Response(
                    504,
                    request=httpx.Request("POST", url),
                    text="<html><body>504 Gateway Time-out</body></html>",
                )
            return httpx.Response(
                200,
                request=httpx.Request("POST", url),
                json={"code": 0, "data": {"fileName": "avatar.png"}},
            )

    async def fake_sleep(_delay):
        return None

    monkeypatch.setattr("services.runninghub_workflow.httpx.AsyncClient", FakeAsyncClient)
    monkeypatch.setattr("services.runninghub_workflow.asyncio.sleep", fake_sleep)

    data = asyncio.run(
        upload_binary_from_url(
            "test-api-key",
            "https://example.com/avatar.png",
            base_url="https://runninghub.example.com",
            retry_delay=0,
        )
    )

    assert data["fileName"] == "avatar.png"
    assert calls == {"get": 1, "post": 2}
