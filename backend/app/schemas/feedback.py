from __future__ import annotations

from pydantic import BaseModel, Field


class FeedbackSummary(BaseModel):
    task_id: str
    metrics: dict[str, float] = Field(default_factory=dict)
