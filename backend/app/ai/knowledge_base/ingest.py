from __future__ import annotations

from app.db.repositories.knowledge_repository import KnowledgeRecord, KnowledgeRepository
from app.utils.hashing import sha256_text


class KnowledgeIngestService:
    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository

    def ingest(self, *, title: str, source: str, content: str, metadata: dict | None = None) -> KnowledgeRecord:
        item_id = f"kb_{sha256_text(title + source + content)[:12]}"
        record = KnowledgeRecord(item_id=item_id, title=title, source=source, content=content, metadata=metadata or {})
        return self.repository.create(record)
