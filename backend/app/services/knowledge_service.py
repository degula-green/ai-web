from __future__ import annotations

from app.adapters.vectorstore.base import BaseVectorStore
from app.ai.knowledge_base.ingest import KnowledgeIngestService
from app.ai.knowledge_base.rerank import KnowledgeReranker
from app.ai.knowledge_base.retrieve import KnowledgeRetriever
from app.db.repositories.knowledge_repository import KnowledgeRepository
from app.schemas.knowledge import KnowledgeQueryResult


class KnowledgeService:
    def __init__(self, *, knowledge_repository: KnowledgeRepository, vector_store: BaseVectorStore) -> None:
        self.repository = knowledge_repository
        self.vector_store = vector_store
        self.ingest_service = KnowledgeIngestService(knowledge_repository)
        self.retriever = KnowledgeRetriever(knowledge_repository)
        self.reranker = KnowledgeReranker()

    def query(self, query: str, *, top_k: int = 3) -> KnowledgeQueryResult:
        hits = self.reranker.rerank(self.retriever.retrieve(query, top_k=top_k))
        return KnowledgeQueryResult(query=query, hits=hits)

    def query_raw(self, query: str, *, top_k: int = 3) -> list[dict]:
        return [hit.model_dump() for hit in self.query(query, top_k=top_k).hits]
