from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class MediaCrawlerJobSpec:
    task_id: str
    platform: str
    crawler_type: str
    keywords: str | None = None
    urls: list[str] = field(default_factory=list)
    enable_comments: bool | None = None
    enable_sub_comments: bool | None = None
    enable_checkpoint: bool | None = None
    checkpoint_id: str | None = None
    timeout_seconds: int = 1800
    env_overrides: dict[str, str] = field(default_factory=dict)
    config_overrides: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "platform": self.platform,
            "crawler_type": self.crawler_type,
            "keywords": self.keywords,
            "urls": self.urls,
            "enable_comments": self.enable_comments,
            "enable_sub_comments": self.enable_sub_comments,
            "enable_checkpoint": self.enable_checkpoint,
            "checkpoint_id": self.checkpoint_id,
            "timeout_seconds": self.timeout_seconds,
            "env_overrides": self.env_overrides,
            "config_overrides": self.config_overrides,
        }


@dataclass(slots=True)
class MediaCrawlerRunResult:
    task_id: str
    command: list[str]
    return_code: int
    summary: dict[str, Any]
    log_path: Path
    output_tail: str

