# -*- coding: utf-8 -*-
"""
本地调用 Content Remix Agent 数字人接口（读库里的 wan2.2-s2v 配置，不写 Key）。

用法（在 backend 目录下）:
  uv run python scripts/test_digital_human_s2v.py

可选:
  uv run python scripts/test_digital_human_s2v.py --base-url http://127.0.0.1:8001
  uv run python scripts/test_digital_human_s2v.py --skip-detect

说明: 若音频为 m4a，DashScope 可能要求 wav/mp3，失败时请看返回的 detail。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# 保证可从 backend 根目录导入（与 run_api_server 一致）
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import httpx

# 用户提供的公网可访问素材（经 download-shared-object 代理）
DEFAULT_IMAGE_URL = (
    "http://47.115.216.167:9090/api/v1/download-shared-object/"
    "aHR0cDovLzEyNy4wLjAuMTo5MDgwL2FpY29udGVudC9DaGF0R1BUJTIwSW1hZ2UlMjAyMDI2JUU1JUI5JUI0MyVFNiU5QyU4ODIzJUU2JTk3JUE1JTIwMTRfMzNfNDQucG5nP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9RjlFNVlLWVZQVDNDMzhYSEdHNUMlMkYyMDI2MDQxOCUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNjA0MThUMDYwMTI5WiZYLUFtei1FeHBpcmVzPTQzMjAwJlgtQW16LVNlY3VyaXR5LVRva2VuPWV5SmhiR2NpT2lKSVV6VXhNaUlzSW5SNWNDSTZJa3BYVkNKOS5leUpoWTJObGMzTkxaWGtpT2lKR09VVTFXVXRaVmxCVU0wTXpPRmhJUjBjMVF5SXNJbVY0Y0NJNk1UYzNOalV6TlRJM05Td2ljR0Z5Wlc1MElqb2liV2x1YVc5aFpHMXBiaUo5LjlLZFdjczBfMHJRMkJzSVh1Tmk2LVZFeWFyN1VGa3lidWhVV0NiYXlVRGdqcnZJdjdNLVpxUFVDNC0tWUxaMDB4aVZoeG5SeHlUQ3lmNnVRUGtMQXlnJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCZ2ZXJzaW9uSWQ9bnVsbCZYLUFtei1TaWduYXR1cmU9MTY1ODBkNmVhNzM2ODczZGM1NGQ3MzhiM2U4ZDI2NTA1OWMzMzViZjY2NWUyY2E4N2MwZTUxYTJkYjhjNzZkMQ"
)

DEFAULT_AUDIO_URL = (
    "http://47.115.216.167:9090/api/v1/download-shared-object/"
    "aHR0cDovLzEyNy4wLjAuMTo5MDgwL2FpY29udGVudC8lRTUlQkQlOTUlRTklOUYlQjMubTRhP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9RjlFNVlLWVZQVDNDMzhYSEdHNUMlMkYyMDI2MDQxOCUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNjA0MThUMDYwMzIzWiZYLUFtei1FeHBpcmVzPTQzMjAwJlgtQW16LVNlY3VyaXR5LVRva2VuPWV5SmhiR2NpT2lKSVV6VXhNaUlzSW5SNWNDSTZJa3BYVkNKOS5leUpoWTJObGMzTkxaWGtpT2lKR09VVTFXVXRaVmxCVU0wTXpPRmhJUjBjMVF5SXNJbVY0Y0NJNk1UYzNOalV6TlRJM05Td2ljR0Z5Wlc1MElqb2liV2x1YVc5aFpHMXBiaUo5LjlLZFdjczBfMHJRMkJzSVh1Tmk2LVZFeWFyN1VGa3lidWhVV0NiYXlVRGdqcnZJdjdNLVpxUFVDNC0tWUxaMDB4aVZoeG5SeHlUQ3lmNnVRUGtMQXlnJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCZ2ZXJzaW9uSWQ9bnVsbCZYLUFtei1TaWduYXR1cmU9MjZmNDYxZDE1YzMxOThiMzY5YjgxMzIyZWZlMjRkZjRhNGVmYTNjNjgwZmU4ZTNkYzI0Y2IwMjUzMzZkNzY0Yw"
)


def main() -> None:
    parser = argparse.ArgumentParser(description="测试数字人 wan2.2-s2v 接口")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001", help="Remix Agent API 根地址")
    parser.add_argument("--config-name", default="wan2.2-s2v", help="llm_configs.config_name")
    parser.add_argument("--skip-detect", action="store_true", help="跳过图像检测直接提交")
    parser.add_argument("--resolution", choices=["480P", "720P"], default="480P")
    parser.add_argument("--style", choices=["speech", "singing", "performance"], default="speech")
    parser.add_argument("--poll-interval", type=float, default=15.0, help="轮询间隔（秒）")
    parser.add_argument("--max-wait", type=float, default=1200.0, help="最长等待（秒），默认 20 分钟")
    parser.add_argument("--image-url", default=DEFAULT_IMAGE_URL)
    parser.add_argument("--audio-url", default=DEFAULT_AUDIO_URL)
    args = parser.parse_args()

    submit_url = f"{args.base_url.rstrip('/')}/api/v1/digital-human/s2v/submit"
    params = {"config_name": args.config_name}
    body = {
        "image_url": args.image_url,
        "audio_url": args.audio_url,
        "resolution": args.resolution,
        "style": args.style,
        "skip_detect": args.skip_detect,
    }

    print("POST", submit_url)
    print("body:", json.dumps({**body, "image_url": body["image_url"][:80] + "…", "audio_url": body["audio_url"][:80] + "…"}, ensure_ascii=False))

    with httpx.Client(timeout=120.0) as client:
        r = client.post(submit_url, params=params, json=body)
        print("status:", r.status_code)
        try:
            data = r.json()
        except Exception:
            print(r.text[:2000])
            raise SystemExit(1)

        print(json.dumps(data, ensure_ascii=False, indent=2))

        if r.status_code >= 400:
            raise SystemExit(1)

        job = data.get("job") or {}
        out = job.get("output") or {}
        task_id = out.get("task_id")
        if not task_id:
            print("未返回 task_id，结束。")
            return

        task_url = f"{args.base_url.rstrip('/')}/api/v1/digital-human/s2v/tasks/{task_id}"
        print("\n轮询 GET", task_url)
        deadline = time.monotonic() + args.max_wait

        while time.monotonic() < deadline:
            tr = client.get(task_url, params=params)
            print("---", time.strftime("%H:%M:%S"), "status", tr.status_code)
            tdata = tr.json()
            print(json.dumps(tdata, ensure_ascii=False, indent=2)[:4000])

            if tr.status_code >= 400:
                raise SystemExit(1)

            tout = (tdata.get("output") or {})
            status = tout.get("task_status")
            if status in ("SUCCEEDED", "FAILED", "UNKNOWN", "CANCELED"):
                if status == "SUCCEEDED":
                    video = (tout.get("results") or {}).get("video_url")
                    print("\n成功，video_url:\n", video)
                return

            time.sleep(args.poll_interval)

        print("超时未结束，请手动查询 task_id:", task_id)


if __name__ == "__main__":
    main()
