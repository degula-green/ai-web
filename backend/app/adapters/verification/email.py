from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from app.adapters.verification.base import BaseEmailProvider, DeliveryReceipt
from app.core.config import EmailSettings


@dataclass(slots=True, frozen=True)
class EmailMessageRecord:
    email: str
    subject: str
    body: str
    code: str
    purpose: str
    ttl_minutes: int


class MockEmailProvider(BaseEmailProvider):
    def __init__(self) -> None:
        self.sent_messages: list[EmailMessageRecord] = []

    def send_verification_code(self, *, email: str, code: str, purpose: str, ttl_minutes: int) -> DeliveryReceipt:
        subject = f"Verification code for {purpose}"
        body = f"Code: {code}\nPurpose: {purpose}\nExpires in {ttl_minutes} minutes."
        self.sent_messages.append(
            EmailMessageRecord(email=email, subject=subject, body=body, code=code, purpose=purpose, ttl_minutes=ttl_minutes)
        )
        print("\n" + "="*50)
        print(f"📧 [MOCK EMAIL] 发送验证码至: {email}")
        print(f"📌 场景: {purpose}")
        print(f"🔢 验证码: {code}")
        print(f"⏳ 有效期: {ttl_minutes} 分钟")
        print("="*50 + "\n")
        
        return DeliveryReceipt(
            provider="mock_email",
            destination=email,
            accepted=True,
            message_id=f"mock-email-{len(self.sent_messages)}",
            detail="mock_sent",
            payload={"purpose": purpose, "ttl_minutes": str(ttl_minutes)},
        )


class SmtpEmailProvider(BaseEmailProvider):
    def __init__(self, settings: EmailSettings) -> None:
        self.settings = settings

    def send_verification_code(self, *, email: str, code: str, purpose: str, ttl_minutes: int) -> DeliveryReceipt:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        
        subject = f"[{self.settings.from_name}] {purpose} verification code"
        body = (
            f"Hello,\n\n"
            f"Your verification code is {code}.\n"
            f"Purpose: {purpose}\n"
            f"Expires in {ttl_minutes} minutes.\n\n"
            f"If you did not request this, ignore this message."
        )
        message = EmailMessage()
        message["From"] = f"{self.settings.from_name} <{self.settings.from_email}>"
        message["To"] = email
        message["Subject"] = subject
        message.set_content(body)

        timeout = 15
        try:
            if self.settings.smtp_use_ssl:
                logger.info("Attempting SMTP_SSL connection to %s:%s", self.settings.smtp_host, self.settings.smtp_port)
                with smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port, timeout=timeout) as client:
                    if self.settings.smtp_username:
                        client.login(self.settings.smtp_username, self.settings.smtp_password)
                    client.send_message(message)
            else:
                logger.info("Attempting SMTP connection to %s:%s", self.settings.smtp_host, self.settings.smtp_port)
                with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=timeout) as client:
                    if self.settings.smtp_use_tls:
                        client.starttls()
                    if self.settings.smtp_username:
                        client.login(self.settings.smtp_username, self.settings.smtp_password)
                    client.send_message(message)
            
            logger.info("Email successfully sent to %s", email)
            return DeliveryReceipt(
                provider="smtp_email",
                destination=email,
                accepted=True,
                detail="sent",
                payload={"purpose": purpose, "ttl_minutes": str(ttl_minutes)},
            )
        except Exception as e:
            logger.error("Failed to send email to %s: %s", email, str(e), exc_info=True)
            return DeliveryReceipt(
                provider="smtp_email",
                destination=email,
                accepted=False,
                detail=str(e),
                payload={"purpose": purpose},
            )

