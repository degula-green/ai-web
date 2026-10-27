from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.knowledge import KnowledgeHit


class BaseKnowledgeBase(ABC):
    @abstractmethod
    def search(self, query: str, *, top_k: int = 3) -> list[KnowledgeHit]:
        raise NotImplementedError
