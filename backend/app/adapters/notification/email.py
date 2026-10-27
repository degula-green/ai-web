from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.adapters.notification.base import BaseEmailProvider, OutboundMessage
from app.core.config import EmailSettings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MockEmailProvider(BaseEmailProvider):
    def send(self, message: OutboundMessage) -> None:
        logger.info("mock email sent to=%s subject=%s content=%s", message.target, message.subject, message.content)


class SMTPEmailProvider(BaseEmailProvider):
    def __init__(self, settings: EmailSettings) -> None:
        self.settings = settings

    def send(self, message: OutboundMessage) -> None:
        email = EmailMessage()
        email["From"] = f"{self.settings.from_name} <{self.settings.from_email}>"
        email["To"] = message.target
        email["Subject"] = message.subject
        email.set_content(message.content)

        if self.settings.smtp_use_ssl:
            server = smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=10)

        with server:
            if self.settings.smtp_use_tls and not self.settings.smtp_use_ssl:
                server.starttls()
            if self.settings.smtp_username:
                server.login(self.settings.smtp_username, self.settings.smtp_password)
            server.send_message(email)


def build_email_provider(settings: EmailSettings) -> BaseEmailProvider:
    if settings.provider == "smtp":
        return SMTPEmailProvider(settings)
    return MockEmailProvider()
