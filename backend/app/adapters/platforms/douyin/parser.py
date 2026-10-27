from __future__ import annotations

from app.adapters.platforms.interfaces import Parser


class DouyinParser(Parser):
    def parse(self, payload: dict) -> dict:
        return {"platform": "douyin", "parsed": True, "payload": payload}
