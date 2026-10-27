from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class DeliveryReceipt:
    provider: str
    destination: str
    accepted: bool = True
    message_id: str | None = None
    detail: str = "sent"
    payload: dict[str, str] = field(default_factory=dict)


class BaseEmailProvider(ABC):
    @abstractmethod
    def send_verification_code(self, *, email: str, code: str, purpose: str, ttl_minutes: int) -> DeliveryReceipt:
        raise NotImplementedError


class BaseSmsProvider(ABC):
    @abstractmethod
    def send_verification_code(self, *, phone_number: str, code: str, purpose: str, ttl_minutes: int) -> DeliveryReceipt:
        raise NotImplementedError

    def verify_verification_code(self, *, phone_number: str, code: str) -> bool:
        raise NotImplementedError

