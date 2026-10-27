from __future__ import annotations

from pathlib import Path

try:
    from langchain_core.prompts import ChatPromptTemplate
except ImportError:  # pragma: no cover - optional dependency in MVP environment
    ChatPromptTemplate = None


PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "knowledge" / "kb_retrieval_prompt.md"


class RAGChain:
    def __init__(self) -> None:
        self.prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
        self.langchain_prompt = (
            ChatPromptTemplate.from_messages([("system", self.prompt_template), ("human", "{query}")])
            if ChatPromptTemplate
            else None
        )

    def run(self, query: str, *, hit_count: int) -> dict[str, str | int]:
        return {"query": query, "hit_count": hit_count, "status": "stubbed"}
