from __future__ import annotations

from abc import ABC, abstractmethod


class Collector(ABC):
    @abstractmethod
    def collect(self, source: str) -> dict:
        raise NotImplementedError


class Parser(ABC):
    @abstractmethod
    def parse(self, payload: dict) -> dict:
        raise NotImplementedError


class Publisher(ABC):
    @abstractmethod
    def publish(self, payload: dict) -> dict:
        raise NotImplementedError


class MetricsCollector(ABC):
    @abstractmethod
    def fetch_metrics(self, task_id: str) -> dict:
        raise NotImplementedError


class PlatformTemplate(ABC):
    @abstractmethod
    def rules(self) -> dict:
        raise NotImplementedError
