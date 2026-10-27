from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass(slots=True)
class MaterialRecord:
    material_id: str
    task_id: str | None
    material_type: str
    source_value: str
    metadata: dict[str, Any] = field(default_factory=dict)


class MaterialRepository:
    def __init__(self) -> None:
        self._store: dict[str, MaterialRecord] = {}
        self._lock = Lock()

    def create(self, record: MaterialRecord) -> MaterialRecord:
        with self._lock:
            self._store[record.material_id] = record
        return record
