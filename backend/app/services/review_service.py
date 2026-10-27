from __future__ import annotations

from app.adapters.llm.base import BaseLLMProvider
from app.ai.chains.review_chain import ReviewChain
from app.ai.routing.model_router import ModelRouter
from app.db.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewPreviewRequest, ReviewResult


class ReviewService:
    def __init__(self, *, llm_provider: BaseLLMProvider, model_router: ModelRouter, review_repository: ReviewRepository) -> None:
        self.llm_provider = llm_provider
        self.model_router = model_router
        self.review_repository = review_repository
        self.chain = ReviewChain()

    def preview(self, payload: ReviewPreviewRequest) -> ReviewResult:
        del self.llm_provider, self.model_router, self.review_repository
        return self.chain.run(payload.content)
