# -*- coding: utf-8 -*-
"""
测试 VideoRetalk 接口（视频 + 音频 -> 新口播视频）。

用法（在 backend 目录）:
  python scripts/test_digital_human_videoretalk.py --base-url http://127.0.0.1:8002
"""
from __future__ import annotations

import argparse
import json
import time

import httpx


DEFAULT_VIDEO_URL = (
    "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20250717/pvegot/input_video_01.mp4"
)
DEFAULT_AUDIO_URL = (
    "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20250717/aumwir/stella2-%E6%9C%89%E5%A3%B0%E4%B9%A67.wav"
)


def main() -> None:
    parser = argparse.ArgumentParser(description="测试 VideoRetalk 接口")
    parser.add_argument("--base-url", default="http://127.0.0.1:8002")
    parser.add_argument("--config-name", default="videoretalk")
    parser.add_argument("--video-url", default=DEFAULT_VIDEO_URL)
    parser.add_argument("--audio-url", default=DEFAULT_AUDIO_URL)
    parser.add_argument("--ref-image-url", default="")
    parser.add_argument("--video-extension", action="store_true")
    parser.add_argument("--query-face-threshold", type=int, default=None)
    parser.add_argument("--poll-interval", type=float, default=12.0)
    parser.add_argument("--max-wait", type=float, default=900.0)
    args = parser.parse_args()

    submit_url = f"{args.base_url.rstrip('/')}/api/v1/digital-human/videoretalk/submit"
    params = {"config_name": args.config_name}
    body = {
        "video_url": args.video_url,
        "audio_url": args.audio_url,
        "video_extension": args.video_extension,
    }
    if args.ref_image_url:
        body["ref_image_url"] = args.ref_image_url
    if args.query_face_threshold is not None:
        body["query_face_threshold"] = args.query_face_threshold

    with httpx.Client(timeout=120.0) as client:
        r = client.post(submit_url, params=params, json=body)
        print("submit status:", r.status_code)
        data = r.json()
        print(json.dumps(data, ensure_ascii=False, indent=2))
        if r.status_code >= 400:
            raise SystemExit(1)

        out = (data.get("job") or {}).get("output") or {}
        task_id = out.get("task_id")
        if not task_id:
            print("未获取到 task_id")
            raise SystemExit(1)

        task_url = f"{args.base_url.rstrip('/')}/api/v1/digital-human/videoretalk/tasks/{task_id}"
        deadline = time.monotonic() + args.max_wait
        while time.monotonic() < deadline:
            tr = client.get(task_url, params=params)
            tdata = tr.json()
            print("poll status:", tr.status_code)
            print(json.dumps(tdata, ensure_ascii=False, indent=2)[:4000])
            if tr.status_code >= 400:
                raise SystemExit(1)

            task_status = (tdata.get("output") or {}).get("task_status")
            if task_status in ("SUCCEEDED", "FAILED", "UNKNOWN", "CANCELED"):
                video_url = ((tdata.get("output") or {}).get("results") or {}).get("video_url")
                if not video_url:
                    video_url = (tdata.get("output") or {}).get("video_url")
                if video_url:
                    print("video_url:", video_url)
                return
            time.sleep(args.poll_interval)

        print("轮询超时，task_id:", task_id)


if __name__ == "__main__":
    main()

