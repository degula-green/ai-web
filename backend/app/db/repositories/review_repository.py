from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass(slots=True)
class ReviewRecord:
    review_id: str
    task_id: str
    decision: str
    summary: str
    details: dict[str, Any] = field(default_factory=dict)


class ReviewRepository:
    def __init__(self) -> None:
        self._store: dict[str, ReviewRecord] = {}
        self._lock = Lock()

    def create(self, record: ReviewRecord) -> ReviewRecord:
        with self._lock:
            self._store[record.review_id] = record
        return record
