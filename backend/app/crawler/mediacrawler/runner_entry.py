from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any


def _load_job_spec(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _apply_env_overrides(env_overrides: dict[str, Any]) -> None:
    for key, value in env_overrides.items():
        if value is None:
            continue
        os.environ[str(key)] = str(value)


def _apply_config_overrides(config_module, overrides: dict[str, Any]) -> None:
    for key, value in overrides.items():
        setattr(config_module, key, value)


def _build_argv(spec: dict[str, Any]) -> list[str]:
    argv = [
        "main.py",
        "--platform",
        str(spec["platform"]),
        "--type",
        str(spec["crawler_type"]),
    ]
    keywords = spec.get("keywords")
    if keywords:
        argv.extend(["--keywords", str(keywords)])

    urls = spec.get("urls") or []
    if urls:
        argv.extend(["--urls", ",".join(str(item) for item in urls)])

    enable_comments = spec.get("enable_comments")
    if enable_comments is True:
        argv.append("--enable_comments")
    elif enable_comments is False:
        argv.append("--no-enable_comments")

    enable_sub_comments = spec.get("enable_sub_comments")
    if enable_sub_comments is True:
        argv.append("--enable_sub_comments")
    elif enable_sub_comments is False:
        argv.append("--no-enable_sub_comments")

    enable_checkpoint = spec.get("enable_checkpoint")
    if enable_checkpoint is True:
        argv.append("--enable_checkpoint")
    elif enable_checkpoint is False:
        argv.append("--no-enable_checkpoint")

    checkpoint_id = spec.get("checkpoint_id")
    if checkpoint_id:
        argv.extend(["--checkpoint_id", str(checkpoint_id)])

    return argv


async def _post_process_results(job_spec: dict[str, Any]) -> None:
    """数据搬运工：将爬虫零散的产出搬运到 Task 专用的暂存货架上"""
    task_id = job_spec.get("task_id")
    platform = job_spec.get("platform")
    if not task_id:
        return

    import redis  # noqa: PLC0415
    
    # 获取连接参数：优先使用内核配置，其次使用环境变量
    try:
        from config import db_config
        host = getattr(db_config, "REDIS_DB_HOST", "127.0.0.1")
        port = int(getattr(db_config, "REDIS_DB_PORT", 6379))
        password = getattr(db_config, "REDIS_DB_PWD", None)
        db_num = int(getattr(db_config, "REDIS_DB_NUM", 0))
    except (ImportError, AttributeError):
        host = os.getenv("REDIS_DB_HOST", "127.0.0.1")
        port = int(os.getenv("REDIS_DB_PORT", 6379))
        password = os.getenv("REDIS_DB_PWD", None)
        db_num = 0

    print(f"[Entry] Connecting Scavenger to Redis: {host}:{port} (db={db_num})")
    r = redis.Redis(
        host=host,
        port=port,
        db=db_num,
        password=password,
        decode_responses=True
    )

    staging_key = f"mediacrawler:staging:{task_id}"
    # 使用更猛的匹配模式：只要带 item 且不论深度的键都搜出来
    # 比如 douyin:crawl:item:hot:index:* 也能被搜到
    pattern = "*:item:*"
    
    print(f"[Entry] Scanning for items with pattern: {pattern}")
    
    count = 0
    # 使用 scan_iter 代替 keys，更安全且能穿透某些 Redis 代理
    for k in r.scan_iter(match=pattern):
        try:
            data_str = r.get(k)
            if not data_str:
                continue
            
            # 推入 backend 识别的暂存列表
            r.rpush(staging_key, data_str)
            # 搬运完清理原始键，保持干净
            r.delete(k)
            count += 1
            if count % 5 == 0:
                print(f"[Entry] Processing... moved {count} items")
        except Exception as e:
            print(f"[Entry] Failed to stage key {k}: {e}")

    # 设置过期时间，防止暂存区无限膨胀 (2小时)
    r.expire(staging_key, 7200)
    print(f"[Entry] Scavenger finished. Successfully staged {count} items for task {task_id}")


async def run_crawler(mc_root: Path, job_spec: dict[str, Any]) -> None:
    os.chdir(mc_root)
    sys.path.insert(0, str(mc_root))

    import config  # noqa: PLC0415
    import main as mc_main  # noqa: PLC0415

    _apply_config_overrides(config, job_spec.get("config_overrides", {}))
    sys.argv = _build_argv(job_spec)

    print("--- Starting MediaCrawler Core ---")
    await mc_main.main()
    print("--- MediaCrawler Core Finished ---")
    
    # 必须在爬虫执行完后的当前 EventLoop 内完成搬运
    await _post_process_results(job_spec)


def main() -> None:
    parser = argparse.ArgumentParser(description="MediaCrawler wrapper entrypoint")
    parser.add_argument("--job-spec", required=True, help="Path to serialized job spec JSON")
    parser.add_argument("--mc-root", required=True, help="crawler-engine root")
    args = parser.parse_args()

    job_spec = _load_job_spec(Path(args.job_spec))
    
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    
    _apply_env_overrides(job_spec.get("env_overrides", {}))

    mc_root = Path(args.mc_root).resolve()

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(run_crawler(mc_root, job_spec))


if __name__ == "__main__":
    main()
