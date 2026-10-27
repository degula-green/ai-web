from __future__ import annotations

from abc import ABC, abstractmethod


class BaseObjectStorage(ABC):
    @abstractmethod
    def upload(self, object_name: str, data: bytes, *, content_type: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_presigned_upload(
        self,
        object_name: str,
        *,
        content_type: str,
        expires_in_seconds: int = 900,
    ) -> tuple[str, str]:
        raise NotImplementedError
