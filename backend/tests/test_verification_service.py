from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.adapters.verification.email import MockEmailProvider
from app.adapters.verification.sms import MockSmsProvider
from app.adapters.verification.store import MemoryVerificationCodeStore
from app.core.config import EmailSettings, SmsSettings, VerificationSettings
from app.core.exceptions import AppError
from app.services.verification_service import EmailService, SmsService


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 4, 3, 0, 0, 0, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self.value

    def advance(self, seconds: int) -> None:
        self.value += timedelta(seconds=seconds)


def build_email_service(clock: Clock, provider: MockEmailProvider | None = None) -> tuple[EmailService, MockEmailProvider]:
    provider = provider or MockEmailProvider()
    service = EmailService(
        provider=provider,
        store=MemoryVerificationCodeStore(clock=clock.now),
        verification_settings=VerificationSettings(
            cache_backend="memory",
            code_length=6,
            code_ttl_seconds=300,
            max_attempts=3,
            mock_fixed_code="123456",
            resend_interval_seconds=60,
        ),
        email_settings=EmailSettings(
            provider="mock",
            from_email="noreply@example.com",
            from_name="AI Content Automation",
            smtp_host="127.0.0.1",
            smtp_port=1025,
            smtp_username="",
            smtp_password="",
            smtp_use_tls=False,
            smtp_use_ssl=False,
        ),
        app_name="AI Content Automation",
        clock=clock.now,
    )
    return service, provider


def build_sms_service(clock: Clock, provider: MockSmsProvider | None = None) -> tuple[SmsService, MockSmsProvider]:
    provider = provider or MockSmsProvider()
    service = SmsService(
        provider=provider,
        store=MemoryVerificationCodeStore(clock=clock.now),
        verification_settings=VerificationSettings(
            cache_backend="memory",
            code_length=6,
            code_ttl_seconds=120,
            max_attempts=2,
            mock_fixed_code="654321",
            resend_interval_seconds=30,
        ),
        sms_settings=SmsSettings(
            provider="mock",
            sign_name="AI内容自动化",
            template_code="SMS_000001",
            access_key_id="",
            access_key_secret="",
            endpoint="dypnsapi.aliyuncs.com",
        ),
        app_name="AI Content Automation",
        clock=clock.now,
    )
    return service, provider


def test_email_send_and_verify_with_mock_provider() -> None:
    clock = Clock()
    service, provider = build_email_service(clock)

    send_result = service.send_verification_code("User@Example.com", purpose="register")
    assert send_result.channel == "email"
    assert send_result.target == "user@example.com"
    assert send_result.delivery_status == "mock_sent"
    assert provider.sent_messages[0].code == "123456"

    verify_result = service.verify_verification_code("user@example.com", purpose="register", code="123456")
    assert verify_result.verified is True
    assert verify_result.reason == "matched"


def test_email_resend_interval_blocks_repeat_send() -> None:
    clock = Clock()
    service, _ = build_email_service(clock)
    service.send_verification_code("user@example.com", purpose="register")

    with pytest.raises(AppError) as exc_info:
        service.send_verification_code("user@example.com", purpose="register")

    assert exc_info.value.code == "verification_rate_limited"


def test_sms_expiry_mismatch_and_locking() -> None:
    clock = Clock()
    service, provider = build_sms_service(clock)

    send_result = service.send_verification_code("13800000001", purpose="login")
    assert send_result.delivery_status == "mock_sent"
    assert provider.sent_messages[0].code == "654321"

    wrong = service.verify_verification_code("13800000001", purpose="login", code="000000")
    assert wrong.verified is False
    assert wrong.reason == "mismatch"
    assert wrong.remaining_attempts == 1

    locked = service.verify_verification_code("13800000001", purpose="login", code="000000")
    assert locked.verified is False
    assert locked.reason == "locked"
    assert locked.remaining_attempts == 0

    service.send_verification_code("13800000001", purpose="login")
    clock.advance(121)
    expired = service.verify_verification_code("13800000001", purpose="login", code="654321")
    assert expired.verified is False
    assert expired.reason == "missing"
