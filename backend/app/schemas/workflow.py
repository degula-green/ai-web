from __future__ import annotations

from pydantic import BaseModel, Field


class WorkflowStep(BaseModel):
    code: str
    label: str
    async_supported: bool = True


class WorkflowBlueprint(BaseModel):
    name: str
    steps: list[WorkflowStep] = Field(default_factory=list)
