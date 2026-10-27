from __future__ import annotations

from app.adapters.llm.base import BaseLLMProvider
from app.ai.chains.parsing_chain import ParsingChain
from app.ai.context.builder import ContextBuilder
from app.ai.routing.model_router import ModelRouter, ModelRoutingRequest
from app.schemas.parse import ParsePreviewRequest, ParseResult


class ParseService:
    def __init__(self, *, llm_provider: BaseLLMProvider, model_router: ModelRouter, context_builder: ContextBuilder) -> None:
        self.llm_provider = llm_provider
        self.model_router = model_router
        self.context_builder = context_builder
        self.chain = ParsingChain()

    def preview(self, payload: ParsePreviewRequest) -> ParseResult:
        route = self.model_router.route(ModelRoutingRequest(task_type="parsing", platform=payload.platform))
        context = self.context_builder.build(task_config={"route_reason": route.reason})
        del self.llm_provider
        return self.chain.run(payload.source_text, platform=payload.platform, context=context)
