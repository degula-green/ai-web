from __future__ import annotations

from app.db.repositories.knowledge_repository import KnowledgeRepository
from app.schemas.knowledge import KnowledgeHit


class KnowledgeRetriever:
    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository

    def retrieve(self, query: str, *, top_k: int = 3) -> list[KnowledgeHit]:
        records = self.repository.search(query, top_k=top_k)
        hits: list[KnowledgeHit] = []
        for index, record in enumerate(records):
            score = max(0.1, 1.0 - (index * 0.1))
            hits.append(KnowledgeHit(item_id=record.item_id, title=record.title, score=score, snippet=record.content[:120]))
        return hits
