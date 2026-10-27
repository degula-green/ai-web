# -*- coding: utf-8 -*-
"""RunningHub workflow client for image-based digital human generation."""

from __future__ import annotations

import io
import asyncio
import mimetypes
from pathlib import PurePosixPath
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx
from PIL import Image

from utils.logger import logger

try:
    import pillow_avif  # type: ignore  # noqa: F401
    AVIF_PLUGIN_AVAILABLE = True
except Exception:
    AVIF_PLUGIN_AVAILABLE = False

DEFAULT_RUNNINGHUB_BASE = "https://www.runninghub.cn"
UPLOAD_BINARY_PATH = "/openapi/v2/media/upload/binary"
RUN_WORKFLOW_PATH = "/openapi/v2/run/workflow"
RUN_AI_APP_PATH = "/openapi/v2/run/ai-app"
QUERY_PATH = "/openapi/v2/query"
RETRYABLE_STATUS_CODES = {502, 503, 504}


def _normalize_base(base_url: Optional[str]) -> str:
    return (base_url or DEFAULT_RUNNINGHUB_BASE).strip().rstrip("/")


def _build_auth_headers(api_key: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


def _guess_filename(source_url: str, content_type: str) -> str:
    parsed = urlparse(source_url)
    name = PurePosixPath(parsed.path).name or "upload"
    if "." in name:
        return name
    guessed_ext = mimetypes.guess_extension(content_type.split(";")[0].strip()) if content_type else None
    return f"{name}{guessed_ext or ''}"


def _should_convert_avif(filename: str, content_type: str) -> bool:
    lower_name = (filename or "").lower()
    lower_type = (content_type or "").lower()
    return lower_name.endswith(".avif") or "image/avif" in lower_type


def _convert_avif_to_png(content: bytes, filename: str) -> tuple[bytes, str, str]:
    if not AVIF_PLUGIN_AVAILABLE:
        raise RuntimeError("AVIF plugin not available")
    image = Image.open(io.BytesIO(content))
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA" if "A" in image.getbands() else "RGB")

    if image.mode == "RGBA":
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.getchannel("A"))
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    output = io.BytesIO()
    image.save(output, format="PNG")
    stem = PurePosixPath(filename or "upload.avif").stem or "upload"
    return output.getvalue(), "image/png", f"{stem}.png"


class RunningHubWorkflowError(Exception):
    """RunningHub HTTP or business error."""

    def __init__(self, message: str, *, status_code: Optional[int] = None, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


def _is_retryable_upstream_response(resp: httpx.Response) -> bool:
    return resp.status_code in RETRYABLE_STATUS_CODES


async def upload_binary_from_url(
    api_key: str,
    source_url: str,
    *,
    base_url: Optional[str] = None,
    timeout: float = 300.0,
    max_retries: int = 2,
    retry_delay: float = 1.5,
) -> Dict[str, Any]:
    root = _normalize_base(base_url)
    upload_url = f"{root}{UPLOAD_BINARY_PATH}"
    attempts = max_retries + 1

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            source_resp = await client.get(source_url)
            source_resp.raise_for_status()
            content = source_resp.content
            content_type = source_resp.headers.get("content-type", "application/octet-stream")
            filename = _guess_filename(source_url, content_type)
            if _should_convert_avif(filename, content_type):
                try:
                    content, content_type, filename = _convert_avif_to_png(content, filename)
                    logger.info("Converted AVIF to PNG before RunningHub upload: {}", filename)
                except Exception as exc:
                    logger.warning("Failed to convert AVIF to PNG for RunningHub upload, fallback to original: {}", exc)

            files = {"file": (filename, content, content_type)}
            resp: httpx.Response | None = None
            for attempt in range(1, attempts + 1):
                resp = await client.post(upload_url, headers=_build_auth_headers(api_key), files=files)
                if not _is_retryable_upstream_response(resp) or attempt >= attempts:
                    break
                logger.warning(
                    "RunningHub upload got retryable status {} for {} (attempt {}/{}), retrying in {}s",
                    resp.status_code,
                    source_url,
                    attempt,
                    attempts,
                    retry_delay,
                )
                await asyncio.sleep(retry_delay)
    except httpx.TimeoutException as exc:
        raise RunningHubWorkflowError(
            f"RunningHub upload timeout after {timeout:.0f}s",
            status_code=504,
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise RunningHubWorkflowError(
            f"Source download failed: HTTP {exc.response.status_code}",
            status_code=exc.response.status_code,
        ) from exc
    except httpx.HTTPError as exc:
        raise RunningHubWorkflowError(f"RunningHub upload request failed: {exc}") from exc

    assert resp is not None

    if _is_retryable_upstream_response(resp):
        logger.warning("RunningHub upload failed after retries with status {}: {}", resp.status_code, resp.text[:500])
        raise RunningHubWorkflowError(
            f"RunningHub upload upstream gateway error: HTTP {resp.status_code}",
            status_code=resp.status_code,
        )

    try:
        data = resp.json()
    except Exception as exc:
        logger.warning("RunningHub upload returned non-JSON: {}", resp.text[:500])
        raise RunningHubWorkflowError(
            f"RunningHub upload returned non-JSON response: {resp.text[:200]}",
            status_code=resp.status_code,
        ) from exc

    if resp.status_code >= 400:
        raise RunningHubWorkflowError(
            str(data.get("message") or data.get("errorMessage") or resp.text[:300]),
            status_code=resp.status_code,
            body=data,
        )
    if data.get("code") not in (0, "0", None):
        raise RunningHubWorkflowError(
            str(data.get("message") or "RunningHub upload failed"),
            status_code=400,
            body=data,
        )

    upload_data = data.get("data") or {}
    if not upload_data.get("fileName"):
        raise RunningHubWorkflowError("RunningHub upload succeeded but fileName is missing", body=data)
    return upload_data


async def submit_workflow(
    api_key: str,
    workflow_id: str,
    node_info_list: list[dict[str, Any]],
    *,
    add_metadata: bool = True,
    instance_type: str = "plus",
    use_personal_queue: bool = False,
    base_url: Optional[str] = None,
    timeout: float = 300.0,
) -> Dict[str, Any]:
    root = _normalize_base(base_url)
    url = f"{root}{RUN_WORKFLOW_PATH}/{workflow_id}"
    payload = {
        "addMetadata": add_metadata,
        "nodeInfoList": node_info_list,
        "instanceType": instance_type,
        "usePersonalQueue": use_personal_queue,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, headers={**_build_auth_headers(api_key), "Content-Type": "application/json"}, json=payload)
    except httpx.TimeoutException as exc:
        raise RunningHubWorkflowError(
            f"RunningHub workflow submit timeout after {timeout:.0f}s",
            status_code=504,
        ) from exc
    except httpx.HTTPError as exc:
        raise RunningHubWorkflowError(f"RunningHub workflow submit failed: {exc}") from exc

    try:
        data = resp.json()
    except Exception as exc:
        logger.warning("RunningHub submit returned non-JSON: {}", resp.text[:500])
        raise RunningHubWorkflowError(
            f"RunningHub submit returned non-JSON response: {resp.text[:200]}",
            status_code=resp.status_code,
        ) from exc

    if resp.status_code >= 400:
        raise RunningHubWorkflowError(
            str(data.get("message") or data.get("errorMessage") or resp.text[:300]),
            status_code=resp.status_code,
            body=data,
        )
    if data.get("errorCode") or data.get("errorMessage"):
        raise RunningHubWorkflowError(
            str(data.get("errorMessage") or data.get("errorCode")),
            status_code=400,
            body=data,
        )
    return data


async def submit_ai_app(
    api_key: str,
    app_id: str,
    node_info_list: list[dict[str, Any]],
    *,
    instance_type: str = "default",
    use_personal_queue: bool = False,
    retain_seconds: int | None = None,
    webhook_url: str | None = None,
    base_url: Optional[str] = None,
    timeout: float = 300.0,
) -> Dict[str, Any]:
    root = _normalize_base(base_url)
    url = f"{root}{RUN_AI_APP_PATH}/{app_id}"
    payload: dict[str, Any] = {
        "nodeInfoList": node_info_list,
        "instanceType": instance_type,
        "usePersonalQueue": use_personal_queue,
    }
    if retain_seconds is not None:
        payload["retainSeconds"] = retain_seconds
    if webhook_url:
        payload["webhookUrl"] = webhook_url

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                url,
                headers={**_build_auth_headers(api_key), "Content-Type": "application/json"},
                json=payload,
            )
    except httpx.TimeoutException as exc:
        raise RunningHubWorkflowError(
            f"RunningHub ai-app submit timeout after {timeout:.0f}s",
            status_code=504,
        ) from exc
    except httpx.HTTPError as exc:
        raise RunningHubWorkflowError(f"RunningHub ai-app submit failed: {exc}") from exc

    try:
        data = resp.json()
    except Exception as exc:
        logger.warning("RunningHub ai-app submit returned non-JSON: {}", resp.text[:500])
        raise RunningHubWorkflowError(
            f"RunningHub ai-app submit returned non-JSON response: {resp.text[:200]}",
            status_code=resp.status_code,
        ) from exc

    if resp.status_code >= 400:
        raise RunningHubWorkflowError(
            str(data.get("message") or data.get("errorMessage") or resp.text[:300]),
            status_code=resp.status_code,
            body=data,
        )
    if data.get("errorCode") or data.get("errorMessage"):
        raise RunningHubWorkflowError(
            str(data.get("errorMessage") or data.get("errorCode")),
            status_code=400,
            body=data,
        )
    return data


async def query_workflow_task(
    api_key: str,
    task_id: str,
    *,
    base_url: Optional[str] = None,
    timeout: float = 120.0,
    retries: int = 2,
) -> Dict[str, Any]:
    root = _normalize_base(base_url)
    url = f"{root}{QUERY_PATH}"
    payload = {"taskId": task_id}
    last_error: RunningHubWorkflowError | None = None

    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    url,
                    headers={**_build_auth_headers(api_key), "Content-Type": "application/json"},
                    json=payload,
                )
        except httpx.TimeoutException as exc:
            last_error = RunningHubWorkflowError(
                f"RunningHub workflow query timeout after {timeout:.0f}s",
                status_code=504,
            )
        except httpx.HTTPError as exc:
            detail = str(exc).strip() or exc.__class__.__name__
            last_error = RunningHubWorkflowError(f"RunningHub workflow query failed: {detail}")
        else:
            try:
                data = resp.json()
            except Exception as exc:
                logger.warning("RunningHub query returned non-JSON: {}", resp.text[:500])
                last_error = RunningHubWorkflowError(
                    f"RunningHub query returned non-JSON response: {resp.text[:200]}",
                    status_code=resp.status_code,
                )
            else:
                if resp.status_code >= 400:
                    last_error = RunningHubWorkflowError(
                        str(data.get("message") or data.get("errorMessage") or resp.text[:300]),
                        status_code=resp.status_code,
                        body=data,
                    )
                else:
                    return data

        if attempt < retries:
            logger.warning(
                "RunningHub query retrying task_id={} attempt={}/{} reason={}",
                task_id,
                attempt + 1,
                retries + 1,
                last_error,
            )

    assert last_error is not None
    raise last_error
