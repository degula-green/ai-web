from __future__ import annotations

from app.adapters.platforms.interfaces import Collector


class DouyinCollector(Collector):
    def collect(self, source: str) -> dict:
        return {"platform": "douyin", "source": source, "status": "stub", "todo": "integrate legacy/prototypes/tiktok"}
