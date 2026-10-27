from __future__ import annotations

from app.ai.memory.manager import MemoryManager
from app.schemas.memory import MemorySnapshot


class MemoryService:
    def __init__(self) -> None:
        self.manager = MemoryManager()

    def record_event(self, *, task_id: str, snapshot_type: str, summary: str, payload: dict | None = None) -> MemorySnapshot:
        return self.manager.record(task_id=task_id, snapshot_type=snapshot_type, summary=summary, payload=payload)

    def summarize_task(self, task_id: str) -> str:
        return self.manager.summarize_task(task_id)
