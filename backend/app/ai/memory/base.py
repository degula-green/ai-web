from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.memory import MemorySnapshot


class BaseTaskMemoryStore(ABC):
    @abstractmethod
    def save(self, snapshot: MemorySnapshot) -> MemorySnapshot:
        raise NotImplementedError

    @abstractmethod
    def list_by_task(self, task_id: str) -> list[MemorySnapshot]:
        raise NotImplementedError
