from __future__ import annotations

from app.adapters.vectorstore.base import BaseVectorStore
from app.core.config import QdrantSettings


class QdrantVectorStoreAdapter(BaseVectorStore):
    def __init__(self, settings: QdrantSettings) -> None:
        self.settings = settings
        self._store: dict[str, dict] = {}

    def upsert(self, item_id: str, vector: list[float], payload: dict) -> None:
        self._store[item_id] = {"vector": vector, "payload": payload}

    def search(self, vector: list[float], *, top_k: int = 3) -> list[dict]:
        del vector
        return list(self._store.values())[:top_k]
