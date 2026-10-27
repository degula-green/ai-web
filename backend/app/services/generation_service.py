from __future__ import annotations

from app.adapters.llm.base import BaseLLMProvider
from app.ai.chains.generation_chain import GenerationChain
from app.ai.context.builder import ContextBuilder
from app.ai.routing.model_router import ModelRouter, ModelRoutingRequest
from app.schemas.generate import GeneratePreviewRequest, GenerateResult
from app.services.knowledge_service import KnowledgeService


class GenerationService:
    def __init__(
        self,
        *,
        llm_provider: BaseLLMProvider,
        model_router: ModelRouter,
        context_builder: ContextBuilder,
        knowledge_service: KnowledgeService,
    ) -> None:
        self.llm_provider = llm_provider
        self.model_router = model_router
        self.context_builder = context_builder
        self.knowledge_service = knowledge_service
        self.chain = GenerationChain()

    def preview(self, payload: GeneratePreviewRequest) -> GenerateResult:
        decision = self.model_router.route(ModelRoutingRequest(task_type="generation", platform=payload.platform))
        hits = self.knowledge_service.query_raw(payload.topic, top_k=3) if payload.use_knowledge else []
        context = self.context_builder.build(knowledge_hits=hits, platform_rules=["短句优先", "开头突出利益点"])
        del self.llm_provider
        return self.chain.run(payload.topic, route_label=f"{decision.provider}/{decision.model}", context=context)
