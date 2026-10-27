from __future__ import annotations

from app.schemas.knowledge import KnowledgeHit


class KnowledgeReranker:
    def rerank(self, hits: list[KnowledgeHit]) -> list[KnowledgeHit]:
        return sorted(hits, key=lambda hit: hit.score, reverse=True)
