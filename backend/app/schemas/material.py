from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MaterialIngestRequest(BaseModel):
    task_id: str | None = None
    material_type: str = "link"
    source_value: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class MaterialRead(BaseModel):
    material_id: str
    task_id: str | None = None
    material_type: str
    source_value: str
    metadata: dict[str, Any] = Field(default_factory=dict)
