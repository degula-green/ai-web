from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class OutboundMessage:
    target: str
    subject: str
    content: str


class BaseEmailProvider:
    def send(self, message: OutboundMessage) -> None:
        raise NotImplementedError


class BaseSmsProvider:
    def send(self, *, phone: str, content: str) -> None:
        raise NotImplementedError
