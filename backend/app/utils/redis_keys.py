from __future__ import annotations


KEYWORD_CACHE_TTL_SECONDS = 60 * 60
HOT_CACHE_TTL_SECONDS = 60 * 60
LOCK_TTL_SECONDS = 15 * 60


def image_item_key(task_no: str, content_id: str) -> str:
    return f"douyin:crawl:item:image:{task_no}:{content_id}"


def video_item_key(task_no: str, content_id: str) -> str:
    return f"douyin:crawl:item:video:{task_no}:{content_id}"


def hot_item_key(snapshot_no: str, rank: int) -> str:
    return f"douyin:hot_rank:rank:{snapshot_no}:{rank}"


def hot_item_index_key(snapshot_no: str) -> str:
    return f"douyin:hot_rank:index:{snapshot_no}"


def image_item_pattern(task_no: str) -> str:
    return f"douyin:crawl:item:image:{task_no}:*"


def video_item_pattern(task_no: str) -> str:
    return f"douyin:crawl:item:video:{task_no}:*"


def hot_item_pattern(snapshot_no: str) -> str:
    return f"douyin:hot_rank:rank:{snapshot_no}:*"


def content_lock_key(content_id: str) -> str:
    return f"douyin:crawl:lock:{content_id}"
