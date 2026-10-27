# -*- coding: utf-8 -*-
"""
阿里云百炼 DashScope — Paraformer-v2 录音文件识别（异步任务 REST）。

文档: https://help.aliyun.com/zh/model-studio/developer-reference/paraformer-recorded-speech-recognition-restful-api

约束: 仅支持公网 HTTP(S) 音视频 URL（不支持本地路径直传）。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx

from utils.logger import logger


@dataclass
class DashScopeParaformerRaw:
    """与 asr_service.RawTranscriptResult 对齐的中间结构，避免循环导入。"""

    text: str
    tokens: List[Tuple[str, int, int]]  # (piece, start_ms, end_ms)

DEFAULT_BASE = "https://dashscope.aliyuncs.com"
TRANSCRIPTION_PATH = "/api/v1/services/audio/asr/transcription"
TASKS_PATH = "/api/v1/tasks"


class DashScopeParaformerError(Exception):
    pass


def _normalize_base(base_url: Optional[str]) -> str:
    return (base_url or DEFAULT_BASE).strip().rstrip("/")


def _require_public_url(file_url: str) -> None:
    u = urlparse(file_url.strip())
    if u.scheme not in ("http", "https"):
        raise DashScopeParaformerError("百炼 Paraformer 仅支持 http(s) 公网 URL")


def _submit_task(client: httpx.Client, api_key: str, file_url: str, base: str) -> str:
    url = f"{base}{TRANSCRIPTION_PATH}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }
    body: Dict[str, Any] = {
        "model": "paraformer-v2",
        "input": {"file_urls": [file_url.strip()]},
        "parameters": {
            "channel_id": [0],
            "language_hints": ["zh", "en"],
        },
    }
    r = client.post(url, headers=headers, json=body, timeout=120.0)
    try:
        data = r.json()
    except Exception as exc:
        raise DashScopeParaformerError(f"提交转写非 JSON: {r.text[:400]}") from exc
    if r.status_code >= 400:
        msg = data.get("message") if isinstance(data, dict) else r.text[:300]
        raise DashScopeParaformerError(f"提交转写失败 HTTP {r.status_code}: {msg}")
    out = data.get("output") or {}
    task_id = out.get("task_id")
    if not task_id:
        raise DashScopeParaformerError(f"提交转写未返回 task_id: {data}")
    return str(task_id)


def _poll_task(
    client: httpx.Client,
    api_key: str,
    task_id: str,
    base: str,
    *,
    interval: float = 1.5,
    max_wait: float = 900.0,
) -> Dict[str, Any]:
    url = f"{base}{TASKS_PATH}/{task_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    deadline = time.monotonic() + max_wait
    while time.monotonic() < deadline:
        r = client.get(url, headers=headers, timeout=60.0)
        try:
            data = r.json()
        except Exception as exc:
            raise DashScopeParaformerError(f"查询任务非 JSON: {r.text[:400]}") from exc
        if r.status_code >= 400:
            msg = data.get("message") if isinstance(data, dict) else r.text[:300]
            raise DashScopeParaformerError(f"查询任务失败 HTTP {r.status_code}: {msg}")
        out = data.get("output") or {}
        status = (out.get("task_status") or "").upper()
        if status == "FAILED":
            raise DashScopeParaformerError(f"转写任务失败: {out}")
        if status == "SUCCEEDED":
            return out
        time.sleep(interval)
    raise DashScopeParaformerError("转写任务超时")


def _pick_transcription_url(output: Dict[str, Any]) -> str:
    results = output.get("results") or []
    for item in results:
        if not isinstance(item, dict):
            continue
        if (item.get("subtask_status") or "").upper() != "SUCCEEDED":
            continue
        tu = item.get("transcription_url")
        if tu:
            return str(tu)
    raise DashScopeParaformerError(f"无可用 transcription_url: {output}")


def parse_transcription_json(payload: Dict[str, Any]) -> DashScopeParaformerRaw:
    """解析百炼结果 JSON（transcription_url 下载体）。"""
    transcripts = payload.get("transcripts") or []
    if not transcripts:
        raise DashScopeParaformerError("识别结果为空（无 transcripts）")
    tr0 = transcripts[0]
    sentences = tr0.get("sentences") or []
    flat: List[Tuple[str, int, int]] = []
    text_parts: List[str] = []

    for sent in sentences:
        if not isinstance(sent, dict):
            continue
        st = (sent.get("text") or "").strip()
        if st:
            text_parts.append(st)
        words = sent.get("words") or []
        if words:
            for w in words:
                if not isinstance(w, dict):
                    continue
                piece = str(w.get("text") or "") + str(w.get("punctuation") or "")
                if not piece.strip():
                    continue
                flat.append(
                    (
                        piece,
                        int(w.get("begin_time", 0)),
                        int(w.get("end_time", 0)),
                    )
                )
        else:
            bt = int(sent.get("begin_time", 0))
            et = int(sent.get("end_time", bt))
            if st:
                flat.append((st, bt, et))

    full_text = "".join(text_parts) if text_parts else "".join(x[0] for x in flat)
    return DashScopeParaformerRaw(text=full_text, tokens=flat)


def transcribe_public_url_sync(
    api_key: str,
    file_url: str,
    *,
    base_url: Optional[str] = None,
    poll_interval: float = 1.5,
    max_wait_seconds: float = 900.0,
) -> DashScopeParaformerRaw:
    """
    对公网可访问的音视频 URL 发起 Paraformer-v2 转写，返回带词级时间戳的 RawTranscriptResult。
    """
    _require_public_url(file_url)
    base = _normalize_base(base_url)
    with httpx.Client(follow_redirects=True) as client:
        task_id = _submit_task(client, api_key, file_url, base)
        logger.info("DashScope Paraformer 任务已提交 task_id=%s", task_id)
        out = _poll_task(
            client,
            api_key,
            task_id,
            base,
            interval=poll_interval,
            max_wait=max_wait_seconds,
        )
        turl = _pick_transcription_url(out)
        tr = client.get(turl, timeout=120.0)
        tr.raise_for_status()
        payload = tr.json()
    if isinstance(payload, str):
        payload = json.loads(payload)
    return parse_transcription_json(payload)
