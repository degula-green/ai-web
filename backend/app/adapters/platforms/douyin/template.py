from __future__ import annotations

from app.adapters.platforms.interfaces import PlatformTemplate


class DouyinTemplate(PlatformTemplate):
    def rules(self) -> dict:
        return {
            "title_max_length": 30,
            "tone": "direct",
            "tags_required": True,
            "cover_ratio": "3:4",
        }
