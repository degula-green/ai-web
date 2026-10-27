from __future__ import annotations

from pydantic import BaseModel, Field


class HealthPayload(BaseModel):
    service: str
    env: str
    version: str
    task_store_backend: str
    integrations: dict[str, str] = Field(default_factory=dict)


class MessagePayload(BaseModel):
    detail: str
