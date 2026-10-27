from __future__ import annotations

from pydantic import BaseModel, Field


class MemorySnapshot(BaseModel):
    snapshot_id: str
    task_id: str
    snapshot_type: str
    summary: str
    payload: dict = Field(default_factory=dict)
