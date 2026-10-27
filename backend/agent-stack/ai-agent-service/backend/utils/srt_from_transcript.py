# -*- coding: utf-8 -*-
"""
将「提取文案」阶段 ASR 产出的 transcript.segments 转为标准 SRT。

segments 项格式: { "start": float 秒, "end": float 秒, "text": str }
与 video_processor_tool / copywriting_service 返回一致。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def format_srt_time(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    ms = int(round((seconds % 1) * 1000))
    total = int(seconds)
    s = total % 60
    total //= 60
    m = total % 60
    h = total // 60
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def segments_to_cues(segments: List[Dict[str, Any]]) -> List[Tuple[float, float, str]]:
    cues: List[Tuple[float, float, str]] = []
    for s in segments:
        if not isinstance(s, dict):
            continue
        try:
            start = float(s["start"])
            end = float(s["end"])
        except (KeyError, TypeError, ValueError):
            continue
        text = str(s.get("text") or "").strip()
        if not text:
            text = "…"
        if end < start:
            end = start
        cues.append((start, end, text))
    return cues


def build_srt_from_cues(cues: List[Tuple[float, float, str]]) -> str:
    lines: list[str] = []
    for i, (start, end, text) in enumerate(cues, start=1):
        safe = text.replace("\r\n", " ").replace("\n", " ").strip()
        lines.append(str(i))
        lines.append(f"{format_srt_time(start)} --> {format_srt_time(end)}")
        lines.append(safe)
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def transcript_dict_to_srt(transcript: Optional[Dict[str, Any]], *, max_chars: int = 500_000) -> Optional[str]:
    """
    从 copywriting extract 返回的 transcript 字段生成 SRT 文本。

    max_chars: 防止异常超大响应；超出则截断并换行追加注释（仍合法 SRT 前几轨可用）。
    """
    if not transcript or not isinstance(transcript, dict):
        return None
    raw = transcript.get("segments")
    if not isinstance(raw, list) or len(raw) == 0:
        return None
    cues = segments_to_cues(raw)
    if not cues:
        return None
    body = build_srt_from_cues(cues)
    if len(body) > max_chars:
        return body[: max_chars - 80] + "\n\n# truncated by server (transcript too long)\n"
    return body
