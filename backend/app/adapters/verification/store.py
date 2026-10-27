from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Callable

from redis import Redis

from app.core.config import RedisSettings
from app.schemas.verification import VerificationCodeRecord


class BaseVerificationCodeStore(ABC):
    @abstractmethod
    def get(self, key: str) -> VerificationCodeRecord | None:
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, record: VerificationCodeRecord, ttl_seconds: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        raise NotImplementedError


class MemoryVerificationCodeStore(BaseVerificationCodeStore):
    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._records: dict[str, VerificationCodeRecord] = {}
        self._lock = threading.Lock()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def get(self, key: str) -> VerificationCodeRecord | None:
        with self._lock:
            record = self._records.get(key)
            if record is None:
                return None
            if record.expires_at <= self._clock():
                self._records.pop(key, None)
                return None
            return record.model_copy(deep=True)

    def set(self, key: str, record: VerificationCodeRecord, ttl_seconds: int) -> None:
        del ttl_seconds
        with self._lock:
            self._records[key] = record.model_copy(deep=True)

    def delete(self, key: str) -> None:
        with self._lock:
            self._records.pop(key, None)


class RedisVerificationCodeStore(BaseVerificationCodeStore):
    def __init__(self, settings: RedisSettings, clock: Callable[[], datetime] | None = None) -> None:
        self.client = Redis(
            host=settings.host,
            port=settings.port,
            db=settings.db,
            username=settings.username or None,
            password=settings.password or None,
            ssl=settings.use_ssl,
            decode_responses=True,
        )
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def get(self, key: str) -> VerificationCodeRecord | None:
        raw = self.client.get(key)
        if raw is None:
            return None
        record = VerificationCodeRecord.model_validate_json(raw)
        if record.expires_at <= self._clock():
            self.delete(key)
            return None
        return record

    def set(self, key: str, record: VerificationCodeRecord, ttl_seconds: int) -> None:
        self.client.set(key, record.model_dump_json(), ex=max(1, ttl_seconds))

    def delete(self, key: str) -> None:
        self.client.delete(key)
