from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.core.constants import DEFAULT_PLATFORM, DEFAULT_SOURCE_TYPE, DEFAULT_TASK_TYPE
from app.core.task_state_machine import TaskState


class TaskCreateRequest(BaseModel):
    task_type: str = DEFAULT_TASK_TYPE
    platform: str = DEFAULT_PLATFORM
    source_type: str = DEFAULT_SOURCE_TYPE
    source_value: str | None = None
    title: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    start_async: bool = False


class TaskTransitionRequest(BaseModel):
    target_state: TaskState


class TaskRead(BaseModel):
    task_id: str
    task_type: str
    platform: str
    source_type: str
    source_value: str | None = None
    title: str | None = None
    state: TaskState
    config: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str
    error_message: str | None = None
