from __future__ import annotations

from app.adapters.platforms.interfaces import MetricsCollector


class DouyinMetricsCollector(MetricsCollector):
    def fetch_metrics(self, task_id: str) -> dict:
        return {"task_id": task_id, "platform": "douyin", "metrics": {}, "status": "stub"}
