from __future__ import annotations

from app.ai.memory.base import BaseTaskMemoryStore
from app.ai.memory.summarizer import MemorySummarizer
from app.schemas.memory import MemorySnapshot
from app.utils.ids import generate_id


class InMemoryTaskMemoryStore(BaseTaskMemoryStore):
    def __init__(self) -> None:
        self._store: dict[str, list[MemorySnapshot]] = {}

    def save(self, snapshot: MemorySnapshot) -> MemorySnapshot:
        self._store.setdefault(snapshot.task_id, []).append(snapshot)
        return snapshot

    def list_by_task(self, task_id: str) -> list[MemorySnapshot]:
        return list(self._store.get(task_id, []))


class MemoryManager:
    def __init__(self, store: BaseTaskMemoryStore | None = None) -> None:
        self.store = store or InMemoryTaskMemoryStore()
        self.summarizer = MemorySummarizer()

    def record(self, *, task_id: str, snapshot_type: str, summary: str, payload: dict | None = None) -> MemorySnapshot:
        snapshot = MemorySnapshot(
            snapshot_id=generate_id("mem"),
            task_id=task_id,
            snapshot_type=snapshot_type,
            summary=summary,
            payload=payload or {},
        )
        return self.store.save(snapshot)

    def summarize_task(self, task_id: str) -> str:
        snapshots = self.store.list_by_task(task_id)
        return self.summarizer.summarize([item.summary for item in snapshots])
