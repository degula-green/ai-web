from __future__ import annotations

from app.adapters.platforms.interfaces import Collector, MetricsCollector, Parser, PlatformTemplate, Publisher


class BilibiliCollector(Collector):
    def collect(self, source: str) -> dict:
        return {"platform": "bilibili", "source": source, "status": "placeholder"}


class BilibiliParser(Parser):
    def parse(self, payload: dict) -> dict:
        return {"platform": "bilibili", "payload": payload, "status": "placeholder"}


class BilibiliPublisher(Publisher):
    def publish(self, payload: dict) -> dict:
        return {"platform": "bilibili", "payload": payload, "status": "placeholder"}


class BilibiliMetricsCollector(MetricsCollector):
    def fetch_metrics(self, task_id: str) -> dict:
        return {"platform": "bilibili", "task_id": task_id, "status": "placeholder"}


class BilibiliTemplate(PlatformTemplate):
    def rules(self) -> dict:
        return {"title_max_length": 80, "tone": "explanatory", "cover_ratio": "16:9"}
