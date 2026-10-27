from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass(slots=True)
class KnowledgeRecord:
    item_id: str
    title: str
    source: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class KnowledgeRepository:
    def __init__(self) -> None:
        self._store: dict[str, KnowledgeRecord] = {}
        self._lock = Lock()
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        if self._store:
            return
        self.create(
            KnowledgeRecord(
                item_id="kb_seed_platform_rule",
                title="Douyin Platform Rule",
                source="seed",
                content="封面要直观、前 3 秒突出卖点、标题尽量简洁、标签围绕垂类关键词。",
                metadata={"category": "platform_rule", "platform": "douyin"},
            )
        )
        self.create(
            KnowledgeRecord(
                item_id="kb_seed_brand_strategy",
                title="Brand Selling Point Memo",
                source="seed",
                content="品牌卖点应拆成痛点、方案、证据、使用场景，并保证视觉素材和文案语气一致。",
                metadata={"category": "brand_knowledge"},
            )
        )

    def create(self, record: KnowledgeRecord) -> KnowledgeRecord:
        with self._lock:
            self._store[record.item_id] = record
        return record

    def search(self, query: str, *, top_k: int = 3) -> list[KnowledgeRecord]:
        lowered = query.lower()
        ranked = sorted(
            self._store.values(),
            key=lambda item: ((lowered in item.title.lower()) + (lowered in item.content.lower()), item.title),
            reverse=True,
        )
        return ranked[:top_k]
