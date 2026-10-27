from __future__ import annotations

from pydantic import BaseModel, Field


class KnowledgeHit(BaseModel):
    item_id: str
    title: str
    score: float
    snippet: str


class KnowledgeQueryRequest(BaseModel):
    query: str
    top_k: int = 3


class KnowledgeQueryResult(BaseModel):
    query: str
    hits: list[KnowledgeHit] = Field(default_factory=list)
