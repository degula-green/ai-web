from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

VerificationChannel = Literal["email", "sms"]


class VerificationSendRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target: str
    purpose: str


class VerificationVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target: str
    purpose: str
    code: str


class VerificationCodeRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: VerificationChannel
    target: str
    purpose: str
    code_hash: str
    provider: str
    sent_at: datetime
    expires_at: datetime
    attempts: int = 0
    last_attempt_at: datetime | None = None
    verified_at: datetime | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class VerificationSendResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: VerificationChannel
    target: str
    purpose: str
    provider: str
    delivery_status: str
    message_id: str | None = None
    sent_at: datetime
    expires_at: datetime
    resend_after: datetime
    expires_in_seconds: int
    resend_interval_seconds: int


class VerificationCheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: VerificationChannel
    target: str
    purpose: str
    verified: bool
    reason: str
    attempts: int
    remaining_attempts: int
    checked_at: datetime
    expires_at: datetime

