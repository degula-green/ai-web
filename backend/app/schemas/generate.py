from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GeneratePreviewRequest(BaseModel):
    task_id: str | None = None
    platform: str = "douyin"
    topic: str
    use_knowledge: bool = True


class GenerateResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    title: str
    body: str
    hashtags: list[str] = Field(default_factory=list)
    model_route: str
