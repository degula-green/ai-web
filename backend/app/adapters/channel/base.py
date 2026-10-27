from __future__ import annotations

from abc import ABC, abstractmethod


class BaseChannelPlugin(ABC):
    @abstractmethod
    def send_message(self, message: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def send_card(self, title: str, body: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def send_review_card(self, task_id: str, status: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def send_alert(self, message: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def receive_callback(self, payload: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def sync_status(self) -> dict:
        raise NotImplementedError
