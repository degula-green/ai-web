from __future__ import annotations

import math
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Callable

from app.adapters.verification.email import MockEmailProvider, SmtpEmailProvider
from app.adapters.verification.sms import AliyunSmsProvider, MockSmsProvider
from app.adapters.verification.store import BaseVerificationCodeStore, MemoryVerificationCodeStore, RedisVerificationCodeStore
from app.adapters.verification.base import BaseEmailProvider, BaseSmsProvider
from app.core.config import EmailSettings, Settings, SmsSettings, VerificationSettings
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.schemas.verification import VerificationCheckResult, VerificationCodeRecord, VerificationSendResult
from app.utils.hashing import sha256_text

logger = get_logger(__name__)


class _BaseVerificationService:
    channel: str

    def __init__(
        self,
        *,
        provider,
        store: BaseVerificationCodeStore,
        verification_settings: VerificationSettings,
        app_name: str,
        clock: Callable[[], datetime] | None = None,
        code_generator: Callable[[int], str] | None = None,
    ) -> None:
        self.provider = provider
        self.store = store
        self.settings = verification_settings
        self.app_name = app_name
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.code_generator = code_generator or self._default_code_generator

    def send_verification_code(self, target: str, *, purpose: str, code: str | None = None) -> VerificationSendResult:
        normalized_target = self._normalize_target(target)
        normalized_purpose = self._normalize_purpose(purpose)
        now = self.clock()
        key = self._cache_key(normalized_target, normalized_purpose)
        existing = self.store.get(key)
        if existing and (now - existing.sent_at).total_seconds() < self.settings.resend_interval_seconds:
            retry_after = self.settings.resend_interval_seconds - int((now - existing.sent_at).total_seconds())
            raise AppError(
                f"验证码发送过于频繁，请在 {retry_after} 秒后重试",
                code="verification_rate_limited",
                status_code=429,
            )

        resolved_code = code or self._resolve_default_code()
        expires_at = now + timedelta(seconds=self.settings.code_ttl_seconds)
        record = VerificationCodeRecord(
            channel=self.channel,
            target=normalized_target,
            purpose=normalized_purpose,
            code_hash=sha256_text(resolved_code),
            provider=self._provider_name(),
            sent_at=now,
            expires_at=expires_at,
        )
        self.store.set(key, record, ttl_seconds=self.settings.code_ttl_seconds)

        try:
            receipt = self._send_to_provider(
                normalized_target,
                resolved_code,
                normalized_purpose,
                ttl_minutes=max(1, math.ceil(self.settings.code_ttl_seconds / 60)),
            )
            if not receipt.accepted:
                logger.error("%s delivery failed: %s", self.channel.upper(), receipt.detail)
                self.store.delete(key)
                raise AppError(
                    f"{self.channel} 验证码发送失败: {receipt.detail}",
                    code="verification_delivery_failed",
                    status_code=502,
                )
        except AppError:
            raise
        except Exception as exc:
            self.store.delete(key)
            logger.exception("Unexpected error in %s delivery", self.channel)
            raise AppError(
                f"{self.channel} 验证码发送失败",
                code="verification_delivery_failed",
                status_code=502,
            ) from exc

        logger.info("verification code sent via %s to %s for %s", receipt.provider, normalized_target, normalized_purpose)
        return VerificationSendResult(
            channel=self.channel,
            target=normalized_target,
            purpose=normalized_purpose,
            provider=receipt.provider,
            delivery_status=receipt.detail,
            message_id=receipt.message_id,
            sent_at=now,
            expires_at=expires_at,
            resend_after=now + timedelta(seconds=self.settings.resend_interval_seconds),
            expires_in_seconds=self.settings.code_ttl_seconds,
            resend_interval_seconds=self.settings.resend_interval_seconds,
        )

    def verify_verification_code(self, target: str, *, purpose: str, code: str) -> VerificationCheckResult:
        normalized_target = self._normalize_target(target)
        normalized_purpose = self._normalize_purpose(purpose)
        now = self.clock()
        key = self._cache_key(normalized_target, normalized_purpose)
        record = self.store.get(key)
        if record is None:
            return self._verification_result(
                normalized_target,
                normalized_purpose,
                verified=False,
                reason="missing",
                attempts=0,
                remaining_attempts=self.settings.max_attempts,
                checked_at=now,
                expires_at=now,
            )

        if record.expires_at <= now:
            self.store.delete(key)
            return self._verification_result(
                normalized_target,
                normalized_purpose,
                verified=False,
                reason="expired",
                attempts=record.attempts,
                remaining_attempts=0,
                checked_at=now,
                expires_at=record.expires_at,
            )

        if record.code_hash == sha256_text(code):
            record.verified_at = now
            self.store.delete(key)
            return self._verification_result(
                normalized_target,
                normalized_purpose,
                verified=True,
                reason="matched",
                attempts=record.attempts,
                remaining_attempts=max(0, self.settings.max_attempts - record.attempts),
                checked_at=now,
                expires_at=record.expires_at,
            )

        record.attempts += 1
        record.last_attempt_at = now
        if record.attempts >= self.settings.max_attempts:
            self.store.delete(key)
            return self._verification_result(
                normalized_target,
                normalized_purpose,
                verified=False,
                reason="locked",
                attempts=record.attempts,
                remaining_attempts=0,
                checked_at=now,
                expires_at=record.expires_at,
            )

        remaining_ttl = max(1, int((record.expires_at - now).total_seconds()))
        self.store.set(key, record, ttl_seconds=remaining_ttl)
        return self._verification_result(
            normalized_target,
            normalized_purpose,
            verified=False,
            reason="mismatch",
            attempts=record.attempts,
            remaining_attempts=max(0, self.settings.max_attempts - record.attempts),
            checked_at=now,
            expires_at=record.expires_at,
        )

    def _verification_result(
        self,
        target: str,
        purpose: str,
        *,
        verified: bool,
        reason: str,
        attempts: int,
        remaining_attempts: int,
        checked_at: datetime,
        expires_at: datetime,
    ) -> VerificationCheckResult:
        return VerificationCheckResult(
            channel=self.channel,
            target=target,
            purpose=purpose,
            verified=verified,
            reason=reason,
            attempts=attempts,
            remaining_attempts=remaining_attempts,
            checked_at=checked_at,
            expires_at=expires_at,
        )

    def _resolve_default_code(self) -> str:
        if self._provider_name().lower().startswith("mock") and self.settings.mock_fixed_code:
            return self.settings.mock_fixed_code
        return self.code_generator(self.settings.code_length)

    def _provider_name(self) -> str:
        return self.provider.__class__.__name__

    @staticmethod
    def _normalize_purpose(purpose: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9]+", "_", purpose.strip().lower()).strip("_")
        if not normalized:
            raise AppError("purpose 不能为空", code="invalid_purpose", status_code=400)
        return normalized

    def _cache_key(self, target: str, purpose: str) -> str:
        return f"verification:{self.channel}:{purpose}:{target}"

    @staticmethod
    def _default_code_generator(length: int) -> str:
        alphabet = "0123456789"
        return "".join(secrets.choice(alphabet) for _ in range(length))


class EmailService(_BaseVerificationService):
    channel = "email"

    def __init__(
        self,
        *,
        provider: BaseEmailProvider,
        store: BaseVerificationCodeStore,
        verification_settings: VerificationSettings,
        email_settings: EmailSettings,
        app_name: str,
        clock: Callable[[], datetime] | None = None,
        code_generator: Callable[[int], str] | None = None,
    ) -> None:
        super().__init__(
            provider=provider,
            store=store,
            verification_settings=verification_settings,
            app_name=app_name,
            clock=clock,
            code_generator=code_generator,
        )
        self.email_settings = email_settings

    def send_verification_code(self, email: str, *, purpose: str, code: str | None = None) -> VerificationSendResult:
        return super().send_verification_code(email, purpose=purpose, code=code)

    def verify_verification_code(self, email: str, *, purpose: str, code: str) -> VerificationCheckResult:
        return super().verify_verification_code(email, purpose=purpose, code=code)

    def _send_to_provider(self, target: str, code: str, purpose: str, ttl_minutes: int):
        return self.provider.send_verification_code(email=target, code=code, purpose=purpose, ttl_minutes=ttl_minutes)

    @staticmethod
    def _normalize_target(target: str) -> str:
        normalized = target.strip().lower()
        if not normalized or "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise AppError("邮箱地址不合法", code="invalid_email", status_code=400)
        return normalized


class SmsService(_BaseVerificationService):
    channel = "sms"

    def __init__(
        self,
        *,
        provider: BaseSmsProvider,
        store: BaseVerificationCodeStore,
        verification_settings: VerificationSettings,
        sms_settings: SmsSettings,
        app_name: str,
        clock: Callable[[], datetime] | None = None,
        code_generator: Callable[[int], str] | None = None,
    ) -> None:
        super().__init__(
            provider=provider,
            store=store,
            verification_settings=verification_settings,
            app_name=app_name,
            clock=clock,
            code_generator=code_generator,
        )
        self.sms_settings = sms_settings

    def send_verification_code(self, phone_number: str, *, purpose: str, code: str | None = None) -> VerificationSendResult:
        return super().send_verification_code(phone_number, purpose=purpose, code=code)

    def verify_verification_code(self, phone_number: str, *, purpose: str, code: str) -> VerificationCheckResult:
        return super().verify_verification_code(phone_number, purpose=purpose, code=code)

    def _send_to_provider(self, target: str, code: str, purpose: str, ttl_minutes: int):
        return self.provider.send_verification_code(phone_number=target, code=code, purpose=purpose, ttl_minutes=ttl_minutes)

    @staticmethod
    def _normalize_target(target: str) -> str:
        normalized = re.sub(r"[\s-]", "", target.strip())
        if not re.fullmatch(r"\+?[0-9]{6,20}", normalized):
            raise AppError("手机号不合法", code="invalid_phone", status_code=400)
        return normalized


class VerificationService:
    def __init__(self, *, settings: Settings, session_factory=None) -> None:
        del session_factory
        self.settings = settings.verification
        self.store = self._build_store(settings)
        self.email_provider = self._build_email_provider(settings.email)
        self.sms_provider = self._build_sms_provider(settings.sms)
        self.email_service = EmailService(
            provider=self.email_provider,
            store=self.store,
            verification_settings=settings.verification,
            email_settings=settings.email,
            app_name=settings.app.name,
        )
        self.sms_service = SmsService(
            provider=self.sms_provider,
            store=self.store,
            verification_settings=settings.verification,
            sms_settings=settings.sms,
            app_name=settings.app.name,
        )

    def send_email_code(self, email: str, *, purpose: str = "login") -> VerificationSendResult:
        return self.email_service.send_verification_code(email, purpose=purpose)

    def verify_email_code(self, email: str, code: str, *, purpose: str = "login") -> VerificationCheckResult:
        result = self.email_service.verify_verification_code(email, purpose=purpose, code=code)
        if not result.verified:
            raise AppError("邮箱验证码校验失败", code="email_code_invalid", status_code=400)
        return result

    def send_sms_code(self, phone_number: str, *, purpose: str = "login") -> VerificationSendResult:
        return self.sms_service.send_verification_code(phone_number, purpose=purpose)

    def verify_sms_code(self, phone_number: str, code: str, *, purpose: str = "login") -> VerificationCheckResult:
        result = self.sms_service.verify_verification_code(phone_number, purpose=purpose, code=code)
        if not result.verified:
            raise AppError("短信验证码校验失败", code="sms_code_invalid", status_code=400)
        return result

    def consume_code(self, channel: str, target: str, code: str, *, purpose: str = "login") -> bool:
        if channel == "email":
            return self.email_service.verify_verification_code(target, purpose=purpose, code=code).verified
        if channel == "sms":
            return self.sms_service.verify_verification_code(target, purpose=purpose, code=code).verified
        raise AppError("不支持的验证码通道", code="invalid_verification_channel", status_code=400)

    @staticmethod
    def _build_store(settings: Settings) -> BaseVerificationCodeStore:
        if settings.verification.cache_backend == "redis":
            return RedisVerificationCodeStore(settings.redis)
        return MemoryVerificationCodeStore()

    @staticmethod
    def _build_email_provider(settings: EmailSettings) -> BaseEmailProvider:
        if settings.provider == "smtp":
            return SmtpEmailProvider(settings)
        return MockEmailProvider()

    @staticmethod
    def _build_sms_provider(settings: SmsSettings) -> BaseSmsProvider:
        if settings.provider == "aliyun":
            return AliyunSmsProvider(settings)
        return MockSmsProvider()
