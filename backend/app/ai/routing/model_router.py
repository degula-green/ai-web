from __future__ import annotations

from dataclasses import dataclass

from app.core.config import LLMSettings


@dataclass(slots=True)
class ModelRoutingRequest:
    task_type: str
    task_level: str = "mvp"
    cost_budget: str = "balanced"
    platform: str = "douyin"
    latency_requirement: str = "normal"


@dataclass(slots=True)
class RouteDecision:
    provider: str
    model: str
    reason: str


class ModelRouter:
    def __init__(self, settings: LLMSettings) -> None:
        self.settings = settings

    def route(self, request: ModelRoutingRequest) -> RouteDecision:
        reason = (
            f"route by task_type={request.task_type}, task_level={request.task_level}, "
            f"platform={request.platform}, latency={request.latency_requirement}"
        )
        return RouteDecision(provider=self.settings.provider, model=self.settings.model, reason=reason)
