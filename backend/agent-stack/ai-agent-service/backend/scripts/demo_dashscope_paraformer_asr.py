# -*- coding: utf-8 -*-
"""
百炼 Paraformer-v2 成片/音频公网 URL 转写演示（需 DASHSCOPE_API_KEY）。

在 backend 目录执行:
  set DASHSCOPE_API_KEY=sk-xxx
  python scripts/demo_dashscope_paraformer_asr.py --url https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/paraformer/hello_world_female2.wav
"""
from __future__ import annotations

import argparse
import os
import sys

# 保证可从 backend 根目录导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        default="https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/paraformer/hello_world_female2.wav",
        help="公网可访问的音视频 URL",
    )
    args = parser.parse_args()
    key = (os.environ.get("DASHSCOPE_API_KEY") or "").strip()
    if not key:
        print("请设置环境变量 DASHSCOPE_API_KEY", file=sys.stderr)
        sys.exit(1)
    from services.dashscope_paraformer_asr import transcribe_public_url_sync

    raw = transcribe_public_url_sync(key, args.url.strip())
    print("--- 全文 ---")
    print(raw.text)
    print("--- 词级片段时间(ms) 前 20 条 ---")
    for i, row in enumerate(raw.tokens[:20]):
        print(i + 1, row)


if __name__ == "__main__":
    main()
