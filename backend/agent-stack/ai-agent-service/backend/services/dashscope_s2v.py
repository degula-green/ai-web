# -*- coding: utf-8 -*-
"""阿里云 DashScope 万相数字人 wan2.2-s2v / wan2.2-s2v-detect HTTP 客户端（异步）。"""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from utils.logger import logger

DEFAULT_DASHSCOPE_BASE = "https://dashscope.aliyuncs.com"

FACE_DETECT_PATH = "/api/v1/services/aigc/image2video/face-detect"
# 与官方 curl 示例一致（带尾部 /）
VIDEO_SYNTHESIS_PATH = "/api/v1/services/aigc/image2video/video-synthesis/"
TASKS_PATH = "/api/v1/tasks"


def _normalize_base(base_url: Optional[str]) -> str:
    b = (base_url or DEFAULT_DASHSCOPE_BASE).strip().rstrip("/")
    return b


class DashScopeS2VError(Exception):
    """DashScope 返回的业务或 HTTP 错误。"""

    def __init__(self, message: str, *, status_code: Optional[int] = None, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


async def face_detect(
    api_key: str,
    image_url: str,
    *,
    base_url: Optional[str] = None,
    timeout: float = 180.0,
) -> Dict[str, Any]:
    """
    同步接口：检测人像图片是否符合 wan2.2-s2v 规范。
    POST .../face-detect，model: wan2.2-s2v-detect
    """
    root = _normalize_base(base_url)
    url = f"{root}{FACE_DETECT_PATH}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "wan2.2-s2v-detect",
        "input": {"image_url": image_url},
    }
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, json=payload, headers=headers)
    except httpx.TimeoutException as e:
        raise DashScopeS2VError(
            f"face-detect 请求超时（>{timeout:.0f}s），请稍后重试或跳过检测",
            status_code=504,
        ) from e
    try:
        data = r.json()
    except Exception:
        raise DashScopeS2VError(f"face-detect 非 JSON 响应: {r.text[:500]}", status_code=r.status_code)

    if r.status_code >= 400:
        raise DashScopeS2VError(
            data.get("message") or data.get("msg") or r.text[:300],
            status_code=r.status_code,
            body=data,
        )
    return data


async def create_video_synthesis_task(
    api_key: str,
    image_url: str,
    audio_url: str,
    *,
    model: str = "wan2.2-s2v",
    resolution: str = "480P",
    style: Optional[str] = "speech",
    base_url: Optional[str] = None,
    timeout: float = 120.0,
) -> Dict[str, Any]:
    """
    异步任务：图 + 音频生成数字人视频。
    Header: X-DashScope-Async: enable
    """
    root = _normalize_base(base_url)
    url = f"{root}{VIDEO_SYNTHESIS_PATH}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }
    parameters: Dict[str, Any] = {"resolution": resolution}
    if style:
        parameters["style"] = style
    payload = {
        "model": model,
        "input": {
            "image_url": image_url,
            "audio_url": audio_url,
        },
        "parameters": parameters,
    }
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, json=payload, headers=headers)
    except httpx.TimeoutException as e:
        raise DashScopeS2VError(
            f"video-synthesis 请求超时（>{timeout:.0f}s），请稍后重试",
            status_code=504,
        ) from e
    try:
        data = r.json()
    except Exception:
        logger.warning("video-synthesis 响应非 JSON: {}", r.text[:500])
        raise DashScopeS2VError(f"video-synthesis 非 JSON 响应: {r.text[:500]}", status_code=r.status_code)

    if r.status_code >= 400:
        msg = (
            (data.get("message") if isinstance(data, dict) else None)
            or (data.get("code") if isinstance(data, dict) else None)
            or r.text[:300]
        )
        raise DashScopeS2VError(str(msg), status_code=r.status_code, body=data)
    return data


async def create_videoretalk_task(
    api_key: str,
    video_url: str,
    audio_url: str,
    *,
    model: str = "videoretalk",
    ref_image_url: Optional[str] = None,
    video_extension: bool = False,
    query_face_threshold: Optional[int] = None,
    base_url: Optional[str] = None,
    timeout: float = 120.0,
) -> Dict[str, Any]:
    """
    异步任务：VideoRetalk（视频 + 音频）口型替换生成。
    POST /api/v1/services/aigc/image2video/video-synthesis/
    Header: X-DashScope-Async: enable
    """
    root = _normalize_base(base_url)
    url = f"{root}{VIDEO_SYNTHESIS_PATH}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }
    input_payload: Dict[str, Any] = {
        "video_url": video_url,
        "audio_url": audio_url,
    }
    if ref_image_url:
        input_payload["ref_image_url"] = ref_image_url

    parameters: Dict[str, Any] = {
        "video_extension": video_extension,
    }
    if query_face_threshold is not None:
        parameters["query_face_threshold"] = query_face_threshold

    payload = {
        "model": model,
        "input": input_payload,
        "parameters": parameters,
    }
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, json=payload, headers=headers)
    except httpx.TimeoutException as e:
        raise DashScopeS2VError(
            f"videoretalk 请求超时（>{timeout:.0f}s），请稍后重试",
            status_code=504,
        ) from e

    try:
        data = r.json()
    except Exception:
        logger.warning("videoretalk 响应非 JSON: {}", r.text[:500])
        raise DashScopeS2VError(f"videoretalk 非 JSON 响应: {r.text[:500]}", status_code=r.status_code)

    if r.status_code >= 400:
        msg = (
            (data.get("message") if isinstance(data, dict) else None)
            or (data.get("code") if isinstance(data, dict) else None)
            or r.text[:300]
        )
        raise DashScopeS2VError(str(msg), status_code=r.status_code, body=data)
    return data


async def get_task(
    api_key: str,
    task_id: str,
    *,
    base_url: Optional[str] = None,
    timeout: float = 60.0,
) -> Dict[str, Any]:
    """GET /api/v1/tasks/{task_id}"""
    root = _normalize_base(base_url)
    url = f"{root}{TASKS_PATH}/{task_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url, headers=headers)
    except httpx.TimeoutException as e:
        raise DashScopeS2VError(
            f"get_task 请求超时（>{timeout:.0f}s），请稍后重试",
            status_code=504,
        ) from e
    try:
        data = r.json()
    except Exception:
        raise DashScopeS2VError(f"get_task 非 JSON 响应: {r.text[:500]}", status_code=r.status_code)

    if r.status_code >= 400:
        msg = data.get("message") if isinstance(data, dict) else r.text[:300]
        raise DashScopeS2VError(str(msg), status_code=r.status_code, body=data)
    return data
