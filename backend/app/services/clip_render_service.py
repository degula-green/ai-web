from __future__ import annotations

import logging
import copy
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.adapters.storage.base import BaseObjectStorage
from app.core.exceptions import ContractError
from app.db.repositories.creation_draft_repository import CreationDraftRecord, CreationDraftRepository
from app.schemas.clip_render import ClipRenderResponse
from app.schemas.review import ReviewClipVideoResponse
from app.schemas.creation_draft import CreationDraftRead
from app.utils.ids import generate_id

logger = logging.getLogger(__name__)

_SUBPROCESS_TEXT_KWARGS: dict[str, Any] = {"text": True, "encoding": "utf-8", "errors": "replace"}
CANVAS_WIDTH = 720
CANVAS_HEIGHT = 1280
DEFAULT_FONT_PATHS = [
    Path(r"C:\Windows\Fonts\msyh.ttc"),
    Path(r"C:\Windows\Fonts\msyhbd.ttc"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]


def _stderr_tail(proc: subprocess.CompletedProcess[str], *, limit: int = 4000) -> str:
    err = proc.stderr
    if not err:
        return ""
    return err[-limit:] if len(err) > limit else err


def _ffmpeg_escape(value: str) -> str:
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace(",", "\\,")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("%", "\\%")
    )


def _pick_drawtext_fontfile() -> str | None:
    for path in DEFAULT_FONT_PATHS:
        if path.is_file():
            return _ffmpeg_escape(str(path.resolve()).replace("\\", "/"))
    return None


def _drawtext_filter(
    *,
    input_label: str,
    output_label: str,
    text: str,
    x: str,
    y: str,
    font_size: int,
    font_color: str,
    border_color: str = "black",
    border_w: int = 3,
    shadow_x: int = 0,
    shadow_y: int = 0,
    box: bool = False,
    box_color: str = "black@0.0",
    box_border_w: int = 20,
    enable: str | None = None,
) -> str:
    escaped_text = _ffmpeg_escape(text)
    fontfile = _pick_drawtext_fontfile()
    parts = [f"{input_label}drawtext=text='{escaped_text}'"]
    if fontfile:
        parts.append(f"fontfile='{fontfile}'")
    parts.extend(
        [
            f"fontsize={font_size}",
            f"fontcolor={font_color}",
            f"x={x}",
            f"y={y}",
            f"bordercolor={border_color}",
            f"borderw={border_w}",
            f"shadowx={shadow_x}",
            f"shadowy={shadow_y}",
        ]
    )
    if box and not _is_transparent_color(box_color):
        parts.extend(
            [
                "box=1",
                f"boxcolor={box_color}",
                f"boxborderw={box_border_w}",
            ]
        )
    if enable:
        parts.append(f"enable='{enable}'")
    return ":".join(parts) + output_label


def _section(config: dict[str, Any], key: str) -> dict[str, Any]:
    value = config.get(key)
    return value if isinstance(value, dict) else {}


def _number(value: Any, default: float, *, minimum: float | None = None, maximum: float | None = None) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        result = default
    if minimum is not None:
        result = max(minimum, result)
    if maximum is not None:
        result = min(maximum, result)
    return result


def _truthy(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _is_transparent_color(value: Any) -> bool:
    raw = str(value or "").strip().lower()
    return raw in {"", "transparent", "none", "null"}


def _safe_color(value: Any, default: str) -> str:
    raw = str(value or "").strip()
    if re.fullmatch(r"#[0-9a-fA-F]{6}", raw):
        return raw
    if re.fullmatch(r"[a-zA-Z]+(@[0-9.]+)?", raw):
        return raw
    return default


def _safe_text(value: Any, fallback: str = "") -> str:
    return str(value or fallback or "").replace("\r\n", " ").replace("\n", " ").strip()


def _scaled_section(config: dict[str, Any], key: str, *, scale_x: float, scale_y: float, scale_font: float) -> None:
    section = _section(config, key)
    if not section:
        return
    for field in ("x", "badgeX"):
        if field in section:
            section[field] = _number(section.get(field), 0) * scale_x
    for field in ("y", "badgeY"):
        if field in section:
            section[field] = _number(section.get(field), 0) * scale_y
    for field in ("fontSize", "subtitleFontSize", "badgeFontSize"):
        if field in section:
            section[field] = max(8, _number(section.get(field), 24) * scale_font)


def _scale_render_config_to_canvas(
    render_config: dict[str, Any],
    *,
    canvas_width: int,
    canvas_height: int,
) -> dict[str, Any]:
    """Map JSON coordinates from the preview design canvas to the real output canvas."""
    canvas_config = _section(render_config, "canvas")
    design_width = int(_number(canvas_config.get("width"), canvas_width, minimum=1))
    design_height = int(_number(canvas_config.get("height"), canvas_height, minimum=1))
    if design_width == canvas_width and design_height == canvas_height:
        return render_config

    scaled = copy.deepcopy(render_config)
    scale_x = canvas_width / design_width
    scale_y = canvas_height / design_height
    scale_font = min(scale_x, scale_y)
    _scaled_section(scaled, "title", scale_x=scale_x, scale_y=scale_y, scale_font=scale_font)
    _scaled_section(scaled, "subtitle", scale_x=scale_x, scale_y=scale_y, scale_font=scale_font)
    scaled["canvas"] = {
        **_section(scaled, "canvas"),
        "width": canvas_width,
        "height": canvas_height,
        "sourceWidth": design_width,
        "sourceHeight": design_height,
    }
    return scaled


def _font_weight_to_border(font_weight: Any) -> int:
    try:
        weight = int(font_weight)
    except (TypeError, ValueError):
        weight = 400
    return 2 if weight >= 700 else 1


def _align_x_expression(*, align: str, x: float, margin: int = 36) -> str:
    offset = int(round(x))
    if align == "center":
        return f"(w-text_w)/2+{offset}"
    if align == "right":
        return f"w-text_w-{margin}+{offset}"
    return f"{margin}+{offset}"


def _apply_render_config_title_filters(
    *,
    base_label: str,
    render_config: dict[str, Any],
    fallback_title: str,
) -> tuple[list[str], str]:
    title_config = _section(render_config, "title")
    if not _truthy(title_config.get("enabled"), False):
        return [], base_label

    title = _safe_text(title_config.get("text"), fallback_title)
    if not title:
        return [], base_label

    subtitle = _safe_text(title_config.get("subtitle"))
    badge = _safe_text(title_config.get("badge"))
    mode = str(title_config.get("mode") or "double")
    align = str(title_config.get("align") or "left")
    x = _number(title_config.get("x"), 0, minimum=-360, maximum=360)
    y = _number(title_config.get("y"), 80, minimum=0, maximum=1180)
    font_size = int(_number(title_config.get("fontSize"), 42, minimum=12, maximum=96))
    subtitle_size = int(_number(title_config.get("subtitleFontSize"), max(18, font_size * 0.58), minimum=10, maximum=72))
    badge_size = int(_number(title_config.get("badgeFontSize"), 22, minimum=10, maximum=48))
    color = _safe_color(title_config.get("color"), "white")
    subtitle_color = _safe_color(title_config.get("subtitleColor"), "white")
    badge_color = _safe_color(title_config.get("badgeColor"), "white")
    border_color = _safe_color(title_config.get("borderColor"), "black@0.48")
    box_color = str(title_config.get("boxColor") or "black@0.36")
    border_w = _font_weight_to_border(title_config.get("fontWeight"))
    filters: list[str] = []
    current = base_label
    index = 0

    def next_label() -> str:
        nonlocal index
        index += 1
        return f"[cfg_title_{index}]"

    if mode == "badge" and badge:
        out = next_label()
        filters.append(
            _drawtext_filter(
                input_label=current,
                output_label=out,
                text=badge[:12],
                x=f"w-text_w-36+{int(_number(title_config.get('badgeX'), 0, minimum=-240, maximum=240))}",
                y=f"36+{int(_number(title_config.get('badgeY'), 0, minimum=-240, maximum=240))}",
                font_size=badge_size,
                font_color=badge_color,
                border_color="#0F766E",
                border_w=1,
                box=True,
                box_color="#0F766E@0.88",
                box_border_w=12,
            )
        )
        current = out

    out = next_label()
    filters.append(
        _drawtext_filter(
            input_label=current,
            output_label=out,
            text=title[:32],
            x=_align_x_expression(align=align.replace("top-", "").replace("bottom-", ""), x=x),
            y=str(int(round(y))),
                font_size=font_size,
                font_color=color,
                border_color=border_color,
                border_w=border_w,
                box=_truthy(title_config.get("box"), False) and not _is_transparent_color(box_color),
                box_color=box_color,
                box_border_w=18,
            )
        )
    current = out

    if mode in {"double", "badge", "bottom"} and subtitle:
        out = next_label()
        filters.append(
            _drawtext_filter(
                input_label=current,
                output_label=out,
                text=subtitle[:32],
                x=_align_x_expression(align=align.replace("top-", "").replace("bottom-", ""), x=x),
                y=str(int(round(y + font_size + 14))),
                font_size=subtitle_size,
                font_color=subtitle_color,
                border_color=border_color,
                border_w=max(1, border_w - 1),
            )
        )
        current = out

    return filters, current


def _subtitle_box_color(mode: str) -> str:
    if mode == "outline":
        return "white@0.90"
    if mode in {"highlight", "brand"}:
        return "#FFF0A8@0.95"
    if mode in {"double", "digital"}:
        return "#0C1E3D@0.82"
    if mode in {"clean", "default"}:
        return "transparent"
    return "black@0.64"


def _subtitle_text_color(mode: str, configured: Any) -> str:
    if configured:
        return _safe_color(configured, "white")
    if mode in {"outline", "highlight", "brand"}:
        return "#0F172A"
    return "white"


def _split_subtitle_lines(text: str, *, double_line: bool) -> list[str]:
    safe = text.strip()
    if not safe:
        return ["..."]
    chars = list(safe)
    if not double_line or len(chars) <= 18:
        return ["".join(chars[:32])]
    midpoint = min(max(12, len(chars) // 2), 22)
    return ["".join(chars[:midpoint]), "".join(chars[midpoint:midpoint + 22])]


def _apply_render_config_subtitle_filters(
    *,
    base_label: str,
    render_config: dict[str, Any],
    cues: list[tuple[float, float, str]],
) -> tuple[list[str], str]:
    subtitle_config = _section(render_config, "subtitle")
    if not _truthy(subtitle_config.get("enabled"), True):
        return [], base_label

    mode = str(subtitle_config.get("mode") or "clean")
    align = str(subtitle_config.get("align") or "center")
    x = _number(subtitle_config.get("x"), 0, minimum=-360, maximum=360)
    y = _number(subtitle_config.get("y"), 1110, minimum=0, maximum=1240)
    font_size = int(_number(subtitle_config.get("fontSize"), 36, minimum=12, maximum=84))
    double_line = _truthy(subtitle_config.get("doubleLine"), False) or mode == "double"
    color = _subtitle_text_color(mode, subtitle_config.get("color"))
    configured_background = subtitle_config.get("background") if "background" in subtitle_config else None
    box_color = str(configured_background) if configured_background is not None else _subtitle_box_color(mode)
    box_enabled = not _is_transparent_color(box_color)
    border_color = _safe_color(subtitle_config.get("borderColor"), "black@0.35")
    border_w = int(_number(subtitle_config.get("borderWidth"), 1 if mode == "outline" else 0, minimum=0, maximum=6))
    filters: list[str] = []
    current = base_label
    index = 0

    for start, end, text in cues:
        lines = _split_subtitle_lines(_safe_text(text, "..."), double_line=double_line)
        line_height = max(font_size + 10, int(font_size * 1.28))
        group_y = y - ((len(lines) - 1) * line_height / 2)
        enable = f"between(t\\,{max(0.0, start):.3f}\\,{max(start, end):.3f})"
        for line_index, line in enumerate(lines):
            index += 1
            out = f"[cfg_sub_{index}]"
            filters.append(
                _drawtext_filter(
                    input_label=current,
                    output_label=out,
                    text=line,
                    x=_align_x_expression(align=align, x=x),
                    y=str(int(round(group_y + (line_index * line_height)))),
                    font_size=font_size,
                    font_color=color,
                    border_color=border_color,
                    border_w=border_w,
                    box=box_enabled,
                    box_color=box_color,
                    box_border_w=max(12, int(font_size * 0.36)),
                    enable=enable,
                )
            )
            current = out
    return filters, current


def _clip_title_template_code(clip_params: dict[str, Any]) -> str:
    return str(clip_params.get("title_template") or "none").strip().lower()


def _apply_title_template_filters(
    *,
    base_label: str,
    clip_params: dict[str, Any],
    canvas_width: int,
    canvas_height: int,
) -> tuple[list[str], str]:
    template_code = _clip_title_template_code(clip_params)
    title = str(clip_params.get("overlay_title") or "").strip()
    subtitle = str(clip_params.get("overlay_subtitle") or "").strip()
    tag = str(clip_params.get("overlay_tag") or "").strip()

    if template_code in {"", "none", "standard"} or not title:
        return [], base_label

    filters: list[str] = []
    current_label = base_label
    top_y = max(36, int(canvas_height * 0.08))
    line_gap = max(12, int(canvas_height * 0.012))
    max_chars = 14
    safe_title = title[: max_chars * 2]
    safe_subtitle = subtitle[: max_chars * 2]
    safe_tag = tag[:12]

    def next_label(index: int) -> str:
        return f"[title_{index}]"

    idx = 0

    if template_code == "headline_white":
        idx += 1
        out = next_label(idx)
        filters.append(
            _drawtext_filter(
                input_label=current_label,
                output_label=out,
                text=safe_title,
                x="(w-text_w)/2",
                y=str(top_y),
                font_size=max(34, int(canvas_width * 0.075)),
                font_color="white",
                border_color="black@0.55",
                border_w=3,
            )
        )
        return filters, out

    if template_code == "headline_white_orange":
        idx += 1
        out = next_label(idx)
        filters.append(
            _drawtext_filter(
                input_label=current_label,
                output_label=out,
                text=safe_title,
                x="(w-text_w)/2",
                y=str(top_y),
                font_size=max(32, int(canvas_width * 0.07)),
                font_color="white",
                border_color="black@0.55",
                border_w=3,
            )
        )
        current_label = out
        if safe_subtitle:
            idx += 1
            out = next_label(idx)
            filters.append(
                _drawtext_filter(
                    input_label=current_label,
                    output_label=out,
                    text=safe_subtitle,
                    x="(w-text_w)/2",
                    y=f"{top_y}+text_h+{line_gap}",
                    font_size=max(36, int(canvas_width * 0.08)),
                    font_color="#FF9A32",
                    border_color="black@0.45",
                    border_w=2,
                )
            )
            current_label = out
        return filters, current_label

    if template_code == "headline_box":
        idx += 1
        out = next_label(idx)
        filters.append(
            _drawtext_filter(
                input_label=current_label,
                output_label=out,
                text=safe_title,
                x="(w-text_w)/2",
                y=str(top_y),
                font_size=max(32, int(canvas_width * 0.068)),
                font_color="white",
                border_color="black@0.35",
                border_w=2,
                box=True,
                box_color="black@0.38",
                box_border_w=24,
            )
        )
        current_label = out
        if safe_subtitle:
            idx += 1
            out = next_label(idx)
            filters.append(
                _drawtext_filter(
                    input_label=current_label,
                    output_label=out,
                    text=safe_subtitle,
                    x="(w-text_w)/2",
                    y=str(top_y + max(64, int(canvas_height * 0.07))),
                    font_size=max(26, int(canvas_width * 0.052)),
                    font_color="#E2E8F0",
                    border_color="black@0.3",
                    border_w=2,
                )
            )
            current_label = out
        return filters, current_label

    if template_code == "headline_tag":
        if safe_tag:
            idx += 1
            out = next_label(idx)
            filters.append(
                _drawtext_filter(
                    input_label=current_label,
                    output_label=out,
                    text=safe_tag,
                    x=f"w-text_w-{max(22, int(canvas_width * 0.04))}",
                    y=str(max(20, int(canvas_height * 0.03))),
                    font_size=max(18, int(canvas_width * 0.03)),
                    font_color="white",
                    border_color="#0F766E",
                    border_w=1,
                    box=True,
                    box_color="#0F766E@0.92",
                    box_border_w=14,
                )
            )
            current_label = out
        idx += 1
        out = next_label(idx)
        filters.append(
            _drawtext_filter(
                input_label=current_label,
                output_label=out,
                text=safe_title,
                x="(w-text_w)/2",
                y=str(top_y),
                font_size=max(32, int(canvas_width * 0.068)),
                font_color="white",
                border_color="black@0.55",
                border_w=3,
            )
        )
        current_label = out
        if safe_subtitle:
            idx += 1
            out = next_label(idx)
            filters.append(
                _drawtext_filter(
                    input_label=current_label,
                    output_label=out,
                    text=safe_subtitle,
                    x="(w-text_w)/2",
                    y=str(top_y + max(60, int(canvas_height * 0.065))),
                    font_size=max(36, int(canvas_width * 0.078)),
                    font_color="#FF8A24",
                    border_color="black@0.45",
                    border_w=2,
                )
            )
            current_label = out
        return filters, current_label

    if template_code == "headline_gold":
        idx += 1
        out = next_label(idx)
        filters.append(
            _drawtext_filter(
                input_label=current_label,
                output_label=out,
                text=safe_title,
                x="(w-text_w)/2",
                y=str(top_y),
                font_size=max(36, int(canvas_width * 0.074)),
                font_color="#F4C542",
                border_color="#5B3A00",
                border_w=3,
            )
        )
        current_label = out
        if safe_subtitle:
            idx += 1
            out = next_label(idx)
            filters.append(
                _drawtext_filter(
                    input_label=current_label,
                    output_label=out,
                    text=safe_subtitle,
                    x="(w-text_w)/2",
                    y=str(top_y + max(64, int(canvas_height * 0.07))),
                    font_size=max(26, int(canvas_width * 0.05)),
                    font_color="white",
                    border_color="black@0.35",
                    border_w=2,
                )
            )
            current_label = out
        return filters, current_label

    return [], base_label


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


def split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    parts = re.split(r"(?<=[。！？，!?])\s*|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def map_rewritten_to_segments(rewritten: str, segments: list[dict[str, Any]]) -> list[tuple[float, float, str]]:
    text = rewritten.strip()
    if not text:
        return [
            (float(s["start"]), float(s["end"]), (str(s.get("text") or "").strip() or "..."))
            for s in segments
        ]

    weights = [max(0.001, float(s["end"]) - float(s["start"])) for s in segments]
    total_weight = sum(weights)
    total_chars = len(text)
    out: list[tuple[float, float, str]] = []
    pos = 0
    for index, segment in enumerate(segments):
        if index == len(segments) - 1:
            chunk = text[pos:]
        else:
            share = int(round(total_chars * weights[index] / total_weight))
            share = max(0, min(share, total_chars - pos))
            chunk = text[pos : pos + share]
            pos += share
        out.append((float(segment["start"]), float(segment["end"]), chunk.strip() or "..."))
    return out


def build_cues_equal_split(rewritten: str, duration: float) -> list[tuple[float, float, str]]:
    lines = split_sentences(rewritten)
    if not lines or duration <= 0:
        return []
    weights = [max(1, len(line)) for line in lines]
    total_weight = sum(weights)
    cues: list[tuple[float, float, str]] = []
    current = 0.0
    for line, weight in zip(lines, weights):
        seg_duration = duration * (weight / total_weight) if total_weight else duration / len(lines)
        end = min(duration, current + seg_duration)
        cues.append((current, end, line))
        current = end
    if cues:
        start, _, text = cues[-1]
        cues[-1] = (start, duration, text)
    return cues


def build_srt_content(cues: list[tuple[float, float, str]]) -> str:
    lines: list[str] = []
    for index, (start, end, text) in enumerate(cues, start=1):
        safe = text.replace("\r\n", " ").replace("\n", " ").strip()
        lines.append(str(index))
        lines.append(f"{format_srt_time(start)} --> {format_srt_time(end)}")
        lines.append(safe)
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _staging_dir_for_clip() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("SYSTEMROOT", "C:\\Windows")) / "Temp"
    else:
        base = Path(tempfile.gettempdir())
    work = base / f"ai_clip_{generate_id('tmp')}"
    work.mkdir(parents=True, exist_ok=True)
    return work


def _subtitles_vf_arg(srt_path: Path, *, force_style: str | None = None) -> str:
    path = srt_path.resolve().as_posix()
    if os.name == "nt" and len(path) > 1 and path[1] == ":":
        path = path[0] + "\\:" + path[2:]
    result = f"subtitles='{path}':charenc=UTF-8"
    if force_style:
        escaped_style = force_style.replace("'", "\\'")
        result += f":force_style='{escaped_style}'"
    return result


def ffprobe_duration_seconds(media_url: str) -> float:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            media_url,
        ],
        check=False,
        capture_output=True,
        timeout=120,
        **_SUBPROCESS_TEXT_KWARGS,
    )
    if proc.returncode != 0:
        logger.warning("ffprobe duration failed: %s", _stderr_tail(proc))
        raise ContractError("Unable to read media duration", status_code=400)
    raw = (proc.stdout or "").strip()
    try:
        return float(raw)
    except ValueError as exc:
        raise ContractError("Unable to parse media duration", status_code=400) from exc


def _ffprobe_has_audio_stream(media_path: Path) -> bool:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(media_path),
        ],
        check=False,
        capture_output=True,
        timeout=120,
        **_SUBPROCESS_TEXT_KWARGS,
    )
    return proc.returncode == 0 and bool((proc.stdout or "").strip())


def _ffprobe_video_size(media_path: Path) -> tuple[int, int]:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=p=0:s=x",
            str(media_path),
        ],
        check=False,
        capture_output=True,
        timeout=120,
        **_SUBPROCESS_TEXT_KWARGS,
    )
    if proc.returncode != 0:
        raise ContractError("Unable to read video size", status_code=400)
    raw = (proc.stdout or "").strip()
    try:
        width_raw, height_raw = raw.split("x", 1)
        width = int(width_raw)
        height = int(height_raw)
    except Exception as exc:  # noqa: BLE001
        raise ContractError("Unable to parse video size", status_code=400) from exc
    if width <= 0 or height <= 0:
        raise ContractError("Invalid video size", status_code=400)
    return width, height


def _is_public_http_media_url(url: str) -> bool:
    parsed = urlparse((url or "").strip())
    if parsed.scheme not in ("http", "https"):
        return False
    host = (parsed.hostname or "").lower()
    if not host or host in {"localhost", "127.0.0.1", "::1"}:
        return False
    if host.endswith(".localhost"):
        return False
    return True


def pick_public_asr_media_url_for_clip(*, voice_params: dict[str, Any], digital_human_params: dict[str, Any]) -> str | None:
    voice = voice_params or {}
    digital = digital_human_params or {}
    for key in ("source_audio_url", "audio_url"):
        value = voice.get(key)
        if isinstance(value, str) and _is_public_http_media_url(value):
            return value.strip()
    for key in ("generated_video_url", "video_url"):
        value = digital.get(key)
        if isinstance(value, str) and _is_public_http_media_url(value):
            return value.strip()
    return None


def segments_dicts_to_cues(segments: list[dict[str, Any]]) -> list[tuple[float, float, str]]:
    cues: list[tuple[float, float, str]] = []
    for segment in segments:
        if not isinstance(segment, dict):
            continue
        try:
            start = float(segment["start"])
            end = float(segment["end"])
        except (KeyError, TypeError, ValueError):
            continue
        cues.append((start, max(start, end), str(segment.get("text") or "").strip() or "..."))
    return cues


def normalize_timeline_segments(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    normalized: list[dict[str, Any]] = []
    for segment in raw:
        if not isinstance(segment, dict):
            continue
        try:
            start = float(segment["start"])
            end = float(segment["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if end <= start:
            continue
        normalized.append(
            {
                "start": start,
                "end": end,
                "text": str(segment.get("text") or "").strip(),
            }
        )
    return normalized


def _download_to(url: str, dest: Path) -> None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AIContentAutomation/1.0"})
        with urllib.request.urlopen(req, timeout=300) as resp:
            dest.write_bytes(resp.read())
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ContractError(f"Failed to download media: {exc}", status_code=400) from exc


def _run_scene_replace(
    *,
    backend_root: Path,
    source_video: Path,
    background_mode: str,
    background_asset: Path,
    output_video: Path,
    draft_id: str,
    output_width: int,
    output_height: int,
) -> None:
    service_root = backend_root / "scene_replace_service"
    runner_path = service_root / "run_scene_replace.py"
    if not runner_path.is_file():
        raise ContractError("scene_replace_service runner not found", status_code=500)

    python_bin = _resolve_scene_replace_python(backend_root)

    command = [
        python_bin,
        str(runner_path),
        "--source-video",
        str(source_video),
        "--output-video",
        str(output_video),
        "--output-width",
        str(output_width),
        "--output-height",
        str(output_height),
        "--task-id",
        draft_id,
    ]
    if background_mode == "video_fill":
        command.extend(["--background-video", str(background_asset)])
    else:
        command.extend(["--background-image", str(background_asset)])

    proc = subprocess.run(
        command,
        cwd=str(service_root),
        check=False,
        capture_output=True,
        timeout=3600,
        **_SUBPROCESS_TEXT_KWARGS,
    )
    if proc.returncode != 0 or not output_video.is_file():
        logger.error(
            "scene replace failed (rc=%s, python=%s): stdout=%s stderr=%s",
            proc.returncode,
            python_bin,
            proc.stdout,
            proc.stderr,
        )
        raise ContractError(
            f"Scene replace failed. Ensure dependencies are installed for interpreter: {python_bin}",
            status_code=500,
        )


def _resolve_scene_replace_python(backend_root: Path) -> str:
    configured = (os.environ.get("SCENE_REPLACE_PYTHON") or "").strip()
    if configured:
        return configured

    candidates: list[Path] = []
    workspace_root = backend_root.parent
    if os.name == "nt":
        candidates.extend([
            Path(r"C:\Program Files\Python311\python.exe"),
            Path(r"C:\Users\杜潇楠\AppData\Local\Programs\Python\Python312\python.exe"),
            workspace_root / ".venv" / "Scripts" / "python.exe",
            backend_root / ".venv" / "Scripts" / "python.exe",
            backend_root / "scene_replace_service" / ".venv" / "Scripts" / "python.exe",
        ])
    else:
        candidates.extend([
            workspace_root / ".venv" / "bin" / "python",
            backend_root / ".venv" / "bin" / "python",
            backend_root / "scene_replace_service" / ".venv" / "bin" / "python",
        ])

    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)

    return "python"


def _subtitle_force_style(mode: str) -> str | None:
    if mode == "brand":
        return (
            "FontName=Microsoft YaHei,"
            "FontSize=18,"
            "PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H004A2A12,"
            "BackColour=&H80331B0C,"
            "Bold=1,"
            "BorderStyle=3,"
            "Outline=1.4,"
            "Shadow=0,"
            "MarginV=56,"
            "Alignment=2"
        )
    if mode == "digital":
        return (
            "FontName=Microsoft YaHei,"
            "FontSize=18,"
            "PrimaryColour=&H00E9FF00,"
            "OutlineColour=&H006C2900,"
            "BackColour=&H801F1808,"
            "Bold=1,"
            "BorderStyle=3,"
            "Outline=1.2,"
            "Shadow=0,"
            "MarginV=56,"
            "Alignment=2"
        )
    return None


class ClipRenderService:
    def __init__(
        self,
        *,
        repository: CreationDraftRepository,
        storage: BaseObjectStorage,
        backend_root: Path,
    ) -> None:
        self.repository = repository
        self.storage = storage
        self.backend_root = backend_root
        self._clips_dir = backend_root / "runtime" / "creation-clips"
        self._review_clips_dir = self._clips_dir / "review"

    def _to_read(self, record: CreationDraftRecord) -> CreationDraftRead:
        return CreationDraftRead(
            draft_id=record.draft_id,
            user_id=record.user_id,
            title=record.title,
            source_url=record.source_url,
            platform=record.platform,
            content_id=record.content_id,
            content_info=record.content_info,
            transcript=record.transcript,
            extracted_copy=record.extracted_copy,
            rewrite_instruction=record.rewrite_instruction,
            rewritten_copy=record.rewritten_copy,
            voice_params=record.voice_params,
            digital_human_params=record.digital_human_params,
            clip_params=record.clip_params,
            status=record.status,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def build_subtitle_cues(self, record: CreationDraftRecord) -> list[tuple[float, float, str]]:
        transcript = record.transcript or {}
        segments = transcript.get("segments") or []
        rewritten = (record.rewritten_copy or "").strip()
        voice = record.voice_params or {}
        digital = record.digital_human_params or {}
        target_video = (digital.get("generated_video_url") or digital.get("video_url") or "").strip()

        stored_timeline = normalize_timeline_segments(voice.get("timeline_segments"))
        if stored_timeline:
            if rewritten:
                return map_rewritten_to_segments(rewritten, stored_timeline)
            return [(item["start"], item["end"], item["text"] or "...") for item in stored_timeline]

        if rewritten and target_video:
            try:
                duration = ffprobe_duration_seconds(target_video)
                cues = build_cues_equal_split(rewritten, duration)
                if cues:
                    return cues
            except ContractError:
                logger.warning("clip render fallback to transcript segments draft_id=%s", record.draft_id)

        if isinstance(segments, list) and segments:
            normalized: list[dict[str, Any]] = []
            for segment in segments:
                if not isinstance(segment, dict):
                    continue
                try:
                    normalized.append(
                        {
                            "start": float(segment["start"]),
                            "end": float(segment["end"]),
                            "text": str(segment.get("text") or ""),
                        }
                    )
                except (KeyError, TypeError, ValueError):
                    continue
            if normalized:
                if rewritten:
                    return map_rewritten_to_segments(rewritten, normalized)
                return [(item["start"], item["end"], item["text"].strip() or "...") for item in normalized]

        if not rewritten:
            raise ContractError("Missing rewritten copy and transcript segments", status_code=400)

        audio_url = voice.get("local_audio_url") or voice.get("audio_url") or voice.get("source_audio_url") or voice.get("clone_audio_url")
        if not audio_url or not isinstance(audio_url, str):
            raise ContractError("Missing voice audio for subtitle alignment", status_code=400)

        duration = ffprobe_duration_seconds(audio_url.strip())
        return build_cues_equal_split(rewritten, duration)

    def render_for_user(
        self,
        *,
        user_id: int,
        draft_id: str,
        subtitle_segments: list[dict[str, Any]] | None = None,
        render_config: dict[str, Any] | None = None,
        playback_path: str | None = None,
    ) -> ClipRenderResponse:
        if not shutil.which("ffmpeg"):
            raise ContractError("FFmpeg is not installed on the server", status_code=503)

        existing = self.repository.get(draft_id, user_id)
        if existing is None:
            raise ContractError("Creation draft not found", status_code=404)

        digital = existing.digital_human_params or {}
        video_url = digital.get("generated_video_url") or digital.get("video_url")
        if not video_url or not isinstance(video_url, str):
            raise ContractError("Generate the digital human video before clipping", status_code=400)

        if subtitle_segments:
            cues = segments_dicts_to_cues(subtitle_segments)
            if not cues:
                raise ContractError("Injected segments are invalid", status_code=400)
        else:
            cues = self.build_subtitle_cues(existing)
        if not cues:
            raise ContractError("Subtitle cues are empty", status_code=400)

        srt_body = build_srt_content(cues)
        clip_params = existing.clip_params or {}
        effective_render_config = render_config if isinstance(render_config, dict) else _section(clip_params, "render_config")
        clip_render_params = {
            **clip_params,
            "overlay_title": str(clip_params.get("overlay_title") or existing.title or "").strip(),
        }
        background_config = _section(effective_render_config, "background")
        audio_config = _section(effective_render_config, "audio")
        subtitle_mode = str(_section(effective_render_config, "subtitle").get("mode") or clip_params.get("subtitle_mode") or "default")
        background_mode = str(background_config.get("mode") or clip_params.get("background_mode") or "original")
        background_asset_url = str(background_config.get("assetUrl") or clip_params.get("background_asset_url") or "").strip()
        template_mode = str(clip_params.get("template_mode") or "talking_head")
        bgm_asset_url = str(audio_config.get("bgmUrl") or clip_params.get("bgm_asset_url") or "").strip()
        bgm_mode = "uploaded" if bgm_asset_url else str(clip_params.get("bgm_mode") or "none")
        voice_volume = _number(audio_config.get("voiceVolume"), float(clip_params.get("voice_volume") or 1.0), minimum=0.0, maximum=2.0)
        bgm_volume = _number(audio_config.get("bgmVolume"), float(clip_params.get("bgm_volume") or 0.0), minimum=0.0, maximum=2.0)

        playback_requires_auth = False
        clipped_public_url: str | None = None

        work = _staging_dir_for_clip()
        try:
            video_local = work / "foreground.mp4"
            processed_video_local = work / "processed.mp4"
            subtitle_local = work / "subtitle.srt"
            output_local = work / "output.mp4"
            background_local: Path | None = None
            bgm_local: Path | None = None

            subtitle_local.write_text(srt_body, encoding="utf-8")
            _download_to(video_url.strip(), video_local)

            if background_mode in {"image_fill", "video_fill"}:
                if not background_asset_url:
                    raise ContractError("Background asset is required for the selected mode", status_code=400)
                background_local = work / ("background.mp4" if background_mode == "video_fill" else "background.png")
                _download_to(background_asset_url, background_local)

            if bgm_mode == "uploaded":
                if not bgm_asset_url:
                    raise ContractError("Background music file is required", status_code=400)
                bgm_local = work / "bgm.mp3"
                _download_to(bgm_asset_url, bgm_local)

            primary_video_local = video_local
            use_scene_replace = background_mode in {"image_fill", "video_fill"} and background_local is not None
            if use_scene_replace:
                source_width, source_height = _ffprobe_video_size(video_local)
                _run_scene_replace(
                    backend_root=self.backend_root,
                    source_video=video_local,
                    background_mode=background_mode,
                    background_asset=background_local,
                    output_video=processed_video_local,
                    draft_id=draft_id,
                    output_width=source_width,
                    output_height=source_height,
                )
                primary_video_local = processed_video_local

            source_width, source_height = _ffprobe_video_size(primary_video_local)
            effective_template_mode = "talking_head" if use_scene_replace else template_mode
            canvas_config = _section(effective_render_config, "canvas")
            requested_canvas_width = int(_number(canvas_config.get("width"), CANVAS_WIDTH, minimum=1, maximum=7680))
            requested_canvas_height = int(_number(canvas_config.get("height"), CANVAS_HEIGHT, minimum=1, maximum=7680))
            preserve_source_canvas = (
                background_mode == "original"
                and effective_template_mode == "talking_head"
                and str(canvas_config.get("aspectMode") or "source") == "source"
            )
            if preserve_source_canvas or use_scene_replace:
                canvas_width, canvas_height = source_width, source_height
            else:
                canvas_width, canvas_height = requested_canvas_width, requested_canvas_height
            render_config_for_canvas = (
                _scale_render_config_to_canvas(
                    effective_render_config,
                    canvas_width=canvas_width,
                    canvas_height=canvas_height,
                )
                if effective_render_config
                else {}
            )

            command: list[str] = ["ffmpeg", "-y", "-i", str(primary_video_local.resolve())]
            background_input_index: int | None = None
            bgm_input_index: int | None = None
            if background_local and not use_scene_replace:
                background_input_index = 1
                if background_mode == "image_fill":
                    command.extend(["-loop", "1", "-i", str(background_local.resolve())])
                else:
                    command.extend(["-stream_loop", "-1", "-i", str(background_local.resolve())])
            if bgm_local:
                bgm_input_index = 2 if background_input_index is not None else 1
                command.extend(["-stream_loop", "-1", "-i", str(bgm_local.resolve())])

            subtitle_filter = _subtitles_vf_arg(subtitle_local, force_style=_subtitle_force_style(subtitle_mode))
            filter_parts: list[str] = []

            if effective_template_mode == "picture_in_picture":
                if background_input_index is not None:
                    filter_parts.append(
                        f"[{background_input_index}:v]scale={canvas_width}:{canvas_height}:force_original_aspect_ratio=increase,crop={canvas_width}:{canvas_height}[bg]"
                    )
                elif background_mode == "blur_fill":
                    filter_parts.append(
                        f"[0:v]scale={canvas_width}:{canvas_height}:force_original_aspect_ratio=increase,crop={canvas_width}:{canvas_height},boxblur=20:10[bg]"
                    )
                else:
                    filter_parts.append(
                        f"[0:v]scale={canvas_width}:{canvas_height}:force_original_aspect_ratio=increase,crop={canvas_width}:{canvas_height}[bg]"
                    )
                pip_width = max(1, int(canvas_width * 0.38))
                pip_height = max(1, int(canvas_height * 0.38))
                margin_x = max(24, int(canvas_width * 0.05))
                margin_y = max(56, int(canvas_height * 0.10))
                filter_parts.append(f"[0:v]scale={pip_width}:{pip_height}:force_original_aspect_ratio=decrease[fg]")
                filter_parts.append(
                    f"[bg][fg]overlay={canvas_width - pip_width - margin_x}:{canvas_height - pip_height - margin_y}[composed]"
                )
            elif background_mode == "blur_fill":
                filter_parts.append(
                    f"[0:v]scale={canvas_width}:{canvas_height}:force_original_aspect_ratio=increase,crop={canvas_width}:{canvas_height},boxblur=20:10[bg]"
                )
                filter_parts.append(
                    f"[0:v]scale={canvas_width}:{canvas_height}:force_original_aspect_ratio=decrease[fg]"
                )
                filter_parts.append("[bg][fg]overlay=(W-w)/2:(H-h)/2[composed]")
            elif background_input_index is not None:
                filter_parts.append(
                    f"[{background_input_index}:v]scale={canvas_width}:{canvas_height}:force_original_aspect_ratio=increase,crop={canvas_width}:{canvas_height}[bg]"
                )
                filter_parts.append(
                    f"[0:v]scale={max(1, canvas_width - 72)}:{max(1, canvas_height - 220)}:force_original_aspect_ratio=decrease[fg]"
                )
                filter_parts.append("[bg][fg]overlay=(W-w)/2:(H-h)/2[composed]")
            else:
                filter_parts.append(
                    f"[0:v]scale={canvas_width}:{canvas_height}:force_original_aspect_ratio=decrease,pad={canvas_width}:{canvas_height}:(ow-iw)/2:(oh-ih)/2:color=black[composed]"
                )

            if render_config_for_canvas:
                title_filters, title_output_label = _apply_render_config_title_filters(
                    base_label="[composed]",
                    render_config=render_config_for_canvas,
                    fallback_title=str(existing.title or ""),
                )
                filter_parts.extend(title_filters)
                subtitle_filters, subtitle_output_label = _apply_render_config_subtitle_filters(
                    base_label=title_output_label,
                    render_config=render_config_for_canvas,
                    cues=cues,
                )
                filter_parts.extend(subtitle_filters)
                filter_parts.append(f"{subtitle_output_label}null[vout]")
            else:
                title_filters, title_output_label = _apply_title_template_filters(
                    base_label="[composed]",
                    clip_params=clip_render_params,
                    canvas_width=canvas_width,
                    canvas_height=canvas_height,
                )
                filter_parts.extend(title_filters)
                filter_parts.append(f"{title_output_label}{subtitle_filter}[vout]")

            video_has_audio = _ffprobe_has_audio_stream(primary_video_local)
            has_output_audio = False
            if video_has_audio and bgm_input_index is not None and bgm_volume > 0:
                filter_parts.append(f"[0:a]volume={voice_volume:.3f}[voice]")
                filter_parts.append(f"[{bgm_input_index}:a]volume={bgm_volume:.3f},afade=t=in:st=0:d=1.5[bgm]")
                filter_parts.append("[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]")
                has_output_audio = True
            elif video_has_audio:
                filter_parts.append(f"[0:a]volume={voice_volume:.3f}[aout]")
                has_output_audio = True
            elif bgm_input_index is not None and bgm_volume > 0:
                filter_parts.append(f"[{bgm_input_index}:a]volume={bgm_volume:.3f}[aout]")
                has_output_audio = True

            proc = subprocess.run(
                command
                + ["-filter_complex", ";".join(filter_parts), "-map", "[vout]"]
                + (["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"] if has_output_audio else ["-an"])
                + [
                    "-c:v",
                    "libx264",
                    "-preset",
                    "fast",
                    "-crf",
                    "23",
                    "-pix_fmt",
                    "yuv420p",
                    "-shortest",
                    str(output_local.resolve()),
                ],
                capture_output=True,
                timeout=600,
                **_SUBPROCESS_TEXT_KWARGS,
            )
            if proc.returncode != 0:
                logger.error("ffmpeg failed (rc=%s): %s", proc.returncode, _stderr_tail(proc))
                raise ContractError("FFmpeg composition failed", status_code=500)

            data = output_local.read_bytes()
        finally:
            shutil.rmtree(work, ignore_errors=True)

        object_name = "/".join(
            [
                "creation-assets",
                "digital_human",
                "video",
                draft_id,
                f"clip_{generate_id('asset')}.mp4",
            ]
        )

        resolved_playback_path = playback_path.strip() if isinstance(playback_path, str) and playback_path.strip() else None

        if getattr(self.storage, "client", None):
            clipped_public_url = self.storage.upload(object_name, data, content_type="video/mp4")
        else:
            self._clips_dir.mkdir(parents=True, exist_ok=True)
            local_file = self._clips_dir / f"{draft_id}.mp4"
            local_file.write_bytes(data)
            clipped_public_url = None
            playback_requires_auth = True

        clipped_video_playback_path = resolved_playback_path if playback_requires_auth else None
        if clipped_video_playback_path is None and playback_requires_auth:
            clipped_video_playback_path = f"/api/v1/creation-drafts/{draft_id}/clipped-video"
        preview_path = clipped_video_playback_path or clipped_public_url

        merged_clip = {
            **clip_params,
            "render_config": render_config_for_canvas or effective_render_config or None,
            "clipped_video_url": clipped_public_url,
            "clipped_at": datetime.now(timezone.utc).isoformat(),
            "playback_requires_auth": playback_requires_auth,
            "clipped_video_playback_path": clipped_video_playback_path,
            "playback_path": preview_path,
            "output_url": preview_path,
        }

        updated = replace(existing, clip_params=merged_clip)
        saved = self.repository.update(updated)
        return ClipRenderResponse(
            draft=self._to_read(saved),
            srt_preview=srt_body[:8000],
            playback_requires_auth=playback_requires_auth,
        )

    def local_clipped_path(self, draft_id: str) -> Path | None:
        path = self._clips_dir / f"{draft_id}.mp4"
        return path if path.is_file() else None

    def render_review_clip(
        self,
        *,
        user_id: str | None,
        media_url: str,
        delete_segments: list[dict[str, Any]],
    ) -> ReviewClipVideoResponse:
        if not shutil.which("ffmpeg"):
            raise ContractError("FFmpeg is not installed on the server", status_code=503)

        cleaned_media_url = str(media_url or "").strip()
        if not cleaned_media_url:
            raise ContractError("media_url is required", status_code=400)

        work = _staging_dir_for_clip()
        try:
            input_local = work / "source.mp4"
            _download_to(cleaned_media_url, input_local)
            return self._render_review_clip_from_local_input(
                user_id=user_id,
                input_local=input_local,
                delete_segments=delete_segments,
            )
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def render_review_clip_upload(
        self,
        *,
        user_id: str | None,
        source_file_path: Path,
        delete_segments: list[dict[str, Any]],
    ) -> ReviewClipVideoResponse:
        if not shutil.which("ffmpeg"):
            raise ContractError("FFmpeg is not installed on the server", status_code=503)
        if not source_file_path.is_file():
            raise ContractError("source file not found", status_code=400)

        work = _staging_dir_for_clip()
        try:
            input_local = work / "source.mp4"
            shutil.copyfile(source_file_path, input_local)
            return self._render_review_clip_from_local_input(
                user_id=user_id,
                input_local=input_local,
                delete_segments=delete_segments,
            )
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def render_review_avatar_merge_upload(
        self,
        *,
        user_id: str | None,
        base_file_path: Path,
        avatar_file_path: Path,
        overlay_position: str,
        overlay_size_percent: float,
        overlay_shape: str,
    ) -> ReviewClipVideoResponse:
        if not shutil.which("ffmpeg"):
            raise ContractError("FFmpeg is not installed on the server", status_code=503)
        if not base_file_path.is_file():
            raise ContractError("base video not found", status_code=400)
        if not avatar_file_path.is_file():
            raise ContractError("avatar video not found", status_code=400)

        work = _staging_dir_for_clip()
        try:
            base_local = work / "base.mp4"
            avatar_local = work / "avatar.mp4"
            output_local = work / "merged.mp4"
            shutil.copyfile(base_file_path, base_local)
            shutil.copyfile(avatar_file_path, avatar_local)
            self._run_review_avatar_merge_ffmpeg(
                base_path=base_local,
                avatar_path=avatar_local,
                output_path=output_local,
                overlay_position=overlay_position,
                overlay_size_percent=overlay_size_percent,
                overlay_shape=overlay_shape,
            )

            clip_id = generate_id("reviewclip")
            duration = ffprobe_duration_seconds(str(output_local.resolve()))
            self._review_clips_dir.mkdir(parents=True, exist_ok=True)
            final_local = self._review_clips_dir / f"{clip_id}.mp4"
            shutil.copyfile(output_local, final_local)
            return ReviewClipVideoResponse(
                clip_id=clip_id,
                playback_path=f"/api/v1/review/clip-video/{clip_id}",
                playback_requires_auth=True,
                original_duration=round(duration, 2),
                new_duration=round(duration, 2),
                deleted_duration=0,
                saved_percent=0,
            )
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def _render_review_clip_from_local_input(
        self,
        *,
        user_id: str | None,
        input_local: Path,
        delete_segments: list[dict[str, Any]],
    ) -> ReviewClipVideoResponse:
        clip_id = generate_id("reviewclip")
        output_local = input_local.parent / "output.mp4"

        original_duration = ffprobe_duration_seconds(str(input_local.resolve()))
        normalized_deletes = self._normalize_delete_segments(delete_segments, original_duration)
        keep_segments = self._build_keep_segments(normalized_deletes, original_duration)
        if not keep_segments:
            raise ContractError("Delete segments remove the whole video", status_code=400)

        self._run_review_clip_ffmpeg(
            input_path=input_local,
            output_path=output_local,
            keep_segments=keep_segments,
        )

        new_duration = ffprobe_duration_seconds(str(output_local.resolve()))
        deleted_duration = max(0.0, original_duration - new_duration)
        saved_percent = round((deleted_duration / original_duration) * 100, 2) if original_duration > 0 else 0.0

        self._review_clips_dir.mkdir(parents=True, exist_ok=True)
        final_local = self._review_clips_dir / f"{clip_id}.mp4"
        shutil.copyfile(output_local, final_local)
        audio_playback_path = None
        if _ffprobe_has_audio_stream(output_local):
            final_audio_local = self._review_clips_dir / f"{clip_id}.m4a"
            self._extract_review_clip_audio(input_path=output_local, output_path=final_audio_local)
            audio_playback_path = f"/api/v1/review/clip-audio/{clip_id}"

        return ReviewClipVideoResponse(
            clip_id=clip_id,
            playback_path=f"/api/v1/review/clip-video/{clip_id}",
            playback_requires_auth=True,
            audio_playback_path=audio_playback_path,
            audio_playback_requires_auth=True,
            original_duration=round(original_duration, 2),
            new_duration=round(new_duration, 2),
            deleted_duration=round(deleted_duration, 2),
            saved_percent=saved_percent,
        )

    def local_review_clip_path(self, *, user_id: str, clip_id: str) -> Path | None:
        direct_path = self._review_clips_dir / f"{clip_id}.mp4"
        if direct_path.is_file():
            return direct_path
        user_path = self._review_clips_dir / user_id / f"{clip_id}.mp4"
        return user_path if user_path.is_file() else None

    def local_review_clip_audio_path(self, *, user_id: str, clip_id: str) -> Path | None:
        direct_path = self._review_clips_dir / f"{clip_id}.m4a"
        if direct_path.is_file():
            return direct_path
        user_path = self._review_clips_dir / user_id / f"{clip_id}.m4a"
        return user_path if user_path.is_file() else None

    def _normalize_delete_segments(
        self,
        delete_segments: list[dict[str, Any]],
        duration: float,
    ) -> list[tuple[float, float]]:
        normalized: list[tuple[float, float]] = []
        for item in delete_segments:
            if not isinstance(item, dict):
                continue
            try:
                start = max(0.0, float(item.get("start", 0)))
                end = min(duration, float(item.get("end", 0)))
            except (TypeError, ValueError):
                continue
            if end <= start:
                continue
            normalized.append((start, end))

        normalized.sort(key=lambda item: item[0])
        merged: list[tuple[float, float]] = []
        for start, end in normalized:
            if not merged or start > merged[-1][1]:
                merged.append((start, end))
                continue
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        return merged

    def _build_keep_segments(
        self,
        delete_segments: list[tuple[float, float]],
        duration: float,
    ) -> list[tuple[float, float]]:
        if not delete_segments:
            return [(0.0, duration)]

        keep_segments: list[tuple[float, float]] = []
        cursor = 0.0
        for start, end in delete_segments:
            if start > cursor:
                keep_segments.append((cursor, start))
            cursor = max(cursor, end)
        if cursor < duration:
            keep_segments.append((cursor, duration))
        return [(start, end) for start, end in keep_segments if end - start > 0.02]

    def _run_review_clip_ffmpeg(
        self,
        *,
        input_path: Path,
        output_path: Path,
        keep_segments: list[tuple[float, float]],
    ) -> None:
        filter_parts: list[str] = []
        video_labels: list[str] = []
        audio_labels: list[str] = []

        has_audio = _ffprobe_has_audio_stream(input_path)
        for index, (start, end) in enumerate(keep_segments):
            filter_parts.append(
                f"[0:v]trim=start={start:.3f}:end={end:.3f},setpts=PTS-STARTPTS[v{index}]"
            )
            video_labels.append(f"[v{index}]")
            if has_audio:
                filter_parts.append(
                    f"[0:a]atrim=start={start:.3f}:end={end:.3f},asetpts=PTS-STARTPTS[a{index}]"
                )
                audio_labels.append(f"[a{index}]")

        filter_parts.append(f"{''.join(video_labels)}concat=n={len(video_labels)}:v=1:a=0[vout]")
        if has_audio:
            filter_parts.append(f"{''.join(audio_labels)}concat=n={len(audio_labels)}:v=0:a=1[aout]")

        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path.resolve()),
            "-filter_complex",
            ";".join(filter_parts),
            "-map",
            "[vout]",
        ]
        if has_audio:
            command.extend(["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"])
        else:
            command.append("-an")

        command.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                str(output_path.resolve()),
            ]
        )

        proc = subprocess.run(
            command,
            check=False,
            capture_output=True,
            timeout=600,
            **_SUBPROCESS_TEXT_KWARGS,
        )
        if proc.returncode != 0:
            logger.error("review clip ffmpeg failed (rc=%s): %s", proc.returncode, _stderr_tail(proc))
            raise ContractError("FFmpeg clip failed", status_code=500)

    def _extract_review_clip_audio(self, *, input_path: Path, output_path: Path) -> None:
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path.resolve()),
            "-vn",
            "-acodec",
            "copy",
            str(output_path.resolve()),
        ]
        proc = subprocess.run(
            command,
            check=False,
            capture_output=True,
            timeout=300,
            **_SUBPROCESS_TEXT_KWARGS,
        )
        if proc.returncode != 0:
            logger.error("review clip audio extract failed (rc=%s): %s", proc.returncode, _stderr_tail(proc))
            raise ContractError("FFmpeg audio extract failed", status_code=500)

    def _run_review_avatar_merge_ffmpeg(
        self,
        *,
        base_path: Path,
        avatar_path: Path,
        output_path: Path,
        overlay_position: str,
        overlay_size_percent: float,
        overlay_shape: str,
    ) -> None:
        canvas_width, canvas_height = _ffprobe_video_size(base_path)
        if canvas_width % 2:
            canvas_width -= 1
        if canvas_height % 2:
            canvas_height -= 1
        canvas_width = max(canvas_width, 320)
        canvas_height = max(canvas_height, 240)

        size_ratio = min(max(float(overlay_size_percent or 30) / 100, 0.15), 0.65)
        margin = max(16, int(min(canvas_width, canvas_height) * 0.025))
        position_map = {
            "bottom-right": (f"W-w-{margin}", f"H-h-{margin}"),
            "bottom-left": (str(margin), f"H-h-{margin}"),
            "top-right": (f"W-w-{margin}", str(margin)),
            "top-left": (str(margin), str(margin)),
            "custom": (f"W-w-{margin}", f"H-h-{margin}"),
        }
        overlay_x, overlay_y = position_map.get(overlay_position, position_map["bottom-right"])
        shape = str(overlay_shape or "square").strip().lower()
        avatar_width = max(120, int(canvas_width * size_ratio))
        if avatar_width % 2:
            avatar_width -= 1
        avatar_filter = f"[1:v]scale={avatar_width}:-2,setsar=1[avatar]"
        if shape == "circle":
            avatar_filter = (
                f"[1:v]scale={avatar_width}:-2,setsar=1,"
                "format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
                "a='if(lte(pow(X-W/2,2)+pow(Y-H/2,2),pow(min(W,H)/2,2)),255,0)'[avatar]"
            )

        filter_complex = (
            f"[0:v]scale={canvas_width}:{canvas_height}:force_original_aspect_ratio=decrease,"
            f"pad={canvas_width}:{canvas_height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1[base];"
            f"{avatar_filter};"
            f"[base][avatar]overlay=x={overlay_x}:y={overlay_y}:shortest=0:format=auto[vout]"
        )
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(base_path.resolve()),
            "-stream_loop",
            "-1",
            "-i",
            str(avatar_path.resolve()),
            "-filter_complex",
            filter_complex,
            "-map",
            "[vout]",
        ]
        if _ffprobe_has_audio_stream(base_path):
            command.extend(["-map", "0:a?", "-c:a", "aac", "-b:a", "192k"])
        elif _ffprobe_has_audio_stream(avatar_path):
            command.extend(["-map", "1:a?", "-c:a", "aac", "-b:a", "192k", "-shortest"])
        else:
            command.append("-an")
        command.extend([
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-t",
            str(max(ffprobe_duration_seconds(str(base_path.resolve())), 0.1)),
            str(output_path.resolve()),
        ])
        proc = subprocess.run(
            command,
            check=False,
            capture_output=True,
            timeout=900,
            **_SUBPROCESS_TEXT_KWARGS,
        )
        if proc.returncode != 0:
            logger.error("review avatar merge ffmpeg failed (rc=%s): %s", proc.returncode, _stderr_tail(proc))
            raise ContractError("FFmpeg avatar merge failed", status_code=500)
