from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from conf import BASE_DIR
from myUtils.postVideo import (
    post_video_DouYin,
    post_video_ks,
    post_video_tencent,
    post_video_xhs,
)

app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 160 * 1024 * 1024

VIDEO_DIR = Path(BASE_DIR / "videoFile")
COOKIE_DIR = Path(BASE_DIR / "cookiesFile")
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
COOKIE_DIR.mkdir(parents=True, exist_ok=True)

PLATFORM_TYPE_MAP = {
    1: "xhs",
    2: None,
    3: "dy",
    4: "ks",
}


def _is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _platform_domain(platform_name: str | None) -> str:
    mapping = {
        "dy": ".douyin.com",
        "xhs": ".xiaohongshu.com",
        "ks": ".kuaishou.com",
        "bili": ".bilibili.com",
        "wb": ".weibo.com",
        "tieba": ".tieba.baidu.com",
    }
    return mapping.get((platform_name or "").strip().lower(), "")


def _cookie_string_to_storage_state(cookie_string: str, platform_name: str | None) -> dict:
    domain = _platform_domain(platform_name)
    cookies: list[dict] = []
    for part in (cookie_string or "").split(";"):
        if "=" not in part:
            continue
        name, value = part.split("=", 1)
        name = name.strip()
        value = value.strip()
        if not name:
            continue
        cookie = {
            "name": name,
            "value": value,
            "path": "/",
            "httpOnly": False,
            "secure": True,
            "sameSite": "Lax",
        }
        if domain:
            cookie["domain"] = domain
        cookies.append(cookie)
    return {"cookies": cookies, "origins": []}


def _materialize_cookie_file_from_cookie_string(cookie_string: str, platform_name: str | None) -> str:
    filename = f"cookie_{uuid.uuid4().hex}.json"
    filepath = COOKIE_DIR / filename
    state = _cookie_string_to_storage_state(cookie_string, platform_name)
    filepath.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    return filename


def _normalize_account_item(item: object) -> dict | None:
    if isinstance(item, dict):
        if item.get("filePath"):
            return {"mode": "file", "value": str(item["filePath"]).strip()}
        if item.get("cookieFile"):
            return {"mode": "file", "value": str(item["cookieFile"]).strip()}
        if item.get("cookie"):
            return {
                "mode": "cookie",
                "value": str(item["cookie"]).strip(),
                "platform": item.get("platform"),
            }
        if item.get("cookies"):
            return {
                "mode": "cookie",
                "value": str(item["cookies"]).strip(),
                "platform": item.get("platform"),
            }
    text = str(item or "").strip()
    if not text:
        return None
    if text.endswith(".json"):
        return {"mode": "file", "value": text}
    return {"mode": "file", "value": text}


def _resolve_account_list(account_list: list[object], publish_type: int) -> list[str]:
    expected_platform = PLATFORM_TYPE_MAP.get(int(publish_type)) if publish_type else None
    resolved: list[str] = []
    for raw in account_list or []:
        item = _normalize_account_item(raw)
        if not item:
            continue
        if item["mode"] == "file":
            value = str(item["value"]).strip()
            if value:
                resolved.append(value)
            continue
        if item["mode"] == "cookie":
            value = str(item["value"]).strip()
            if value:
                resolved.append(
                    _materialize_cookie_file_from_cookie_string(
                        value,
                        item.get("platform") or expected_platform,
                    )
                )
    return resolved


def _download_to_video_dir(url: str) -> str:
    suffix = Path(urlparse(url).path).suffix or ".mp4"
    filename = f"url_{uuid.uuid4().hex}{suffix}"
    filepath = VIDEO_DIR / filename
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with open(filepath, "wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    return filename


def _materialize_local_video(src: str) -> str:
    source = Path(src)
    if not source.is_absolute():
        candidate = VIDEO_DIR / src
        if candidate.exists():
            return src
        source = (Path.cwd() / src).resolve()
    if not source.exists() or not source.is_file():
        raise RuntimeError(f"video file not found: {src}")
    filename = f"local_{uuid.uuid4().hex}{source.suffix or '.mp4'}"
    target = VIDEO_DIR / filename
    shutil.copy2(source, target)
    return filename


def _resolve_file_list(file_list: list[object]) -> list[str]:
    resolved: list[str] = []
    for raw in file_list or []:
        value = str(raw or "").strip()
        if not value:
            continue
        if _is_url(value):
            resolved.append(_download_to_video_dir(value))
        else:
            resolved.append(_materialize_local_video(value))
    return resolved


def _dispatch_publish(
    publish_type: int,
    *,
    title: str,
    desc: str,
    raw_file_list: list[object],
    raw_account_list: list[object],
    tags: list[str] | None,
    category: int | None,
    enable_timer: bool,
    videos_per_day: int | None,
    daily_times: list[int] | None,
    start_days: int | None,
    is_draft: bool,
    thumbnail_path: str,
    product_link: str,
    product_title: str,
    headless: bool,
) -> None:
    resolved_type = int(publish_type)
    file_list = _resolve_file_list(raw_file_list)
    account_list = _resolve_account_list(raw_account_list, resolved_type)

    if not file_list:
        raise ValueError("file list cannot be empty")
    if not account_list:
        raise ValueError("account list cannot be empty")

    print("Resolved File List:", file_list)
    print("Resolved Account List:", account_list)

    if resolved_type == 1:
        post_video_xhs(
            title,
            desc,
            file_list,
            tags,
            account_list,
            category,
            enable_timer,
            videos_per_day,
            daily_times,
            start_days,
            headless=headless,
        )
        return
    if resolved_type == 2:
        post_video_tencent(
            title,
            desc,
            file_list,
            tags,
            account_list,
            category,
            enable_timer,
            videos_per_day,
            daily_times,
            start_days,
            is_draft,
            headless=headless,
        )
        return
    if resolved_type == 3:
        post_video_DouYin(
            title,
            desc,
            file_list,
            tags,
            account_list,
            category,
            enable_timer,
            videos_per_day,
            daily_times,
            start_days,
            thumbnail_path,
            product_link,
            product_title,
            headless=headless,
        )
        return
    if resolved_type == 4:
        post_video_ks(
            title,
            desc,
            file_list,
            tags,
            account_list,
            category,
            enable_timer,
            videos_per_day,
            daily_times,
            start_days,
            headless=headless,
        )
        return
    raise ValueError(f"unsupported platform type: {resolved_type}")


@app.get("/health")
def health() -> tuple[dict, int]:
    return {"code": 200, "msg": "ok", "data": None}, 200


@app.get("/getFile")
def get_file():
    filename = str(request.args.get("filename") or "").strip()
    if not filename:
        return jsonify({"code": 400, "msg": "filename is required", "data": None}), 400
    if ".." in filename or filename.startswith("/"):
        return jsonify({"code": 400, "msg": "invalid filename", "data": None}), 400
    return send_from_directory(str(VIDEO_DIR), filename)


@app.post("/upload")
def upload_file():
    file = request.files.get("file")
    if file is None:
        return jsonify({"code": 400, "msg": "no file in request", "data": None}), 400
    if not file.filename:
        return jsonify({"code": 400, "msg": "empty filename", "data": None}), 400

    filename = f"{uuid.uuid1()}_{file.filename}"
    filepath = VIDEO_DIR / filename
    file.save(filepath)
    return jsonify({"code": 200, "msg": "uploaded", "data": filename}), 200


@app.post("/postVideo")
def post_video():
    data = request.get_json(silent=True) or {}
    raw_file_list = data.get("fileList") or []
    raw_account_list = data.get("accountList") or []
    publish_type = data.get("type")
    title = str(data.get("title") or "").strip()

    if not publish_type:
        return jsonify({"code": 400, "msg": "platform type is required", "data": None}), 400
    if not title:
        return jsonify({"code": 400, "msg": "title is required", "data": None}), 400

    category = data.get("category")
    if category == 0:
        category = None

    try:
        _dispatch_publish(
            int(publish_type),
            title=title,
            desc=str(data.get("desc") or "").strip(),
            raw_file_list=raw_file_list,
            raw_account_list=raw_account_list,
            tags=data.get("tags") or [],
            category=category,
            enable_timer=bool(data.get("enableTimer")),
            videos_per_day=data.get("videosPerDay"),
            daily_times=data.get("dailyTimes"),
            start_days=data.get("startDays"),
            is_draft=bool(data.get("isDraft", False)),
            thumbnail_path=str(data.get("thumbnail") or "").strip(),
            product_link=str(data.get("productLink") or "").strip(),
            product_title=str(data.get("productTitle") or "").strip(),
            headless=bool(data.get("headless", data.get("publishMode", "headless") != "headed")),
        )
    except Exception as exc:
        print(f"publish error: {exc}")
        return jsonify({"code": 500, "msg": f"publish failed: {exc}", "data": None}), 500

    return jsonify({"code": 200, "msg": "发送成功", "data": None}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5409)
