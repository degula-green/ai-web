from __future__ import annotations

from app.adapters.notification.base import BaseSmsProvider
from app.core.config import SmsSettings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MockSmsProvider(BaseSmsProvider):
    def send(self, *, phone: str, content: str) -> None:
        logger.info("mock sms sent to=%s content=%s", phone, content)


class AliyunSmsProvider(BaseSmsProvider):
    def __init__(self, settings: SmsSettings) -> None:
        self.settings = settings

    def send(self, *, phone: str, content: str) -> None:
        logger.info(
            "aliyun sms provider not enabled in local runtime, target=%s sign=%s template=%s",
            phone,
            self.settings.sign_name,
            self.settings.template_code,
        )


def build_sms_provider(settings: SmsSettings) -> BaseSmsProvider:
    if settings.provider == "aliyun":
        return AliyunSmsProvider(settings)
    return MockSmsProvider()
