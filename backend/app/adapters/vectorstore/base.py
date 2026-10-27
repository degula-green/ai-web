from __future__ import annotations

from abc import ABC, abstractmethod


class BaseVectorStore(ABC):
    @abstractmethod
    def upsert(self, item_id: str, vector: list[float], payload: dict) -> None:
        raise NotImplementedError

    @abstractmethod
    def search(self, vector: list[float], *, top_k: int = 3) -> list[dict]:
        raise NotImplementedError
