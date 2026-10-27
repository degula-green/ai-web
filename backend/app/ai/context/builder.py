from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AIExecutionContext(BaseModel):
    parsed_result: dict[str, Any] = Field(default_factory=dict)
    brand_selling_points: list[str] = Field(default_factory=list)
    knowledge_hits: list[dict[str, Any]] = Field(default_factory=list)
    review_feedback: list[str] = Field(default_factory=list)
    platform_rules: list[str] = Field(default_factory=list)
    task_config: dict[str, Any] = Field(default_factory=dict)


class ContextBuilder:
    def build(
        self,
        *,
        parsed_result: dict[str, Any] | None = None,
        brand_selling_points: list[str] | None = None,
        knowledge_hits: list[dict[str, Any]] | None = None,
        review_feedback: list[str] | None = None,
        platform_rules: list[str] | None = None,
        task_config: dict[str, Any] | None = None,
    ) -> AIExecutionContext:
        return AIExecutionContext(
            parsed_result=parsed_result or {},
            brand_selling_points=brand_selling_points or [],
            knowledge_hits=knowledge_hits or [],
            review_feedback=review_feedback or [],
            platform_rules=platform_rules or [],
            task_config=task_config or {},
        )
