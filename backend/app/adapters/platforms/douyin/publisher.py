from __future__ import annotations

from app.adapters.platforms.interfaces import Publisher


class DouyinPublisher(Publisher):
    def publish(self, payload: dict) -> dict:
        return {"platform": "douyin", "published": False, "payload": payload, "status": "stub"}
