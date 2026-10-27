from __future__ import annotations

from app.adapters.platforms.interfaces import Collector, MetricsCollector, Parser, PlatformTemplate, Publisher


class XiaohongshuCollector(Collector):
    def collect(self, source: str) -> dict:
        return {"platform": "xiaohongshu", "source": source, "status": "placeholder"}


class XiaohongshuParser(Parser):
    def parse(self, payload: dict) -> dict:
        return {"platform": "xiaohongshu", "payload": payload, "status": "placeholder"}


class XiaohongshuPublisher(Publisher):
    def publish(self, payload: dict) -> dict:
        return {"platform": "xiaohongshu", "payload": payload, "status": "placeholder"}


class XiaohongshuMetricsCollector(MetricsCollector):
    def fetch_metrics(self, task_id: str) -> dict:
        return {"platform": "xiaohongshu", "task_id": task_id, "status": "placeholder"}


class XiaohongshuTemplate(PlatformTemplate):
    def rules(self) -> dict:
        return {"title_max_length": 20, "tone": "lifestyle", "cover_ratio": "3:4"}
