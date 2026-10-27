from __future__ import annotations

from app.adapters.channel.base import BaseChannelPlugin
from app.core.config import FeishuSettings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FeishuChannelPlugin(BaseChannelPlugin):
    def __init__(self, settings: FeishuSettings) -> None:
        self.settings = settings

    def send_message(self, message: str) -> None:
        logger.info("Feishu message stub: %s", message)

    def send_card(self, title: str, body: str) -> None:
        logger.info("Feishu card stub: %s | %s", title, body)

    def send_review_card(self, task_id: str, status: str) -> None:
        logger.info("Feishu review card stub: %s | %s", task_id, status)

    def send_alert(self, message: str) -> None:
        logger.warning("Feishu alert stub: %s", message)

    def receive_callback(self, payload: dict) -> dict:
        return {"status": "received", "payload": payload}

    def sync_status(self) -> dict:
        return {"provider": "feishu", "configured": bool(self.settings.webhook)}
