from __future__ import annotations

from pathlib import Path

from app.ai.context.builder import AIExecutionContext
from app.schemas.parse import ParseResult

try:
    from langchain_core.prompts import ChatPromptTemplate
except ImportError:  # pragma: no cover - optional dependency in MVP environment
    ChatPromptTemplate = None


PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "parsing" / "parsing_prompt.md"


class ParsingChain:
    def __init__(self) -> None:
        self.prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
        self.langchain_prompt = (
            ChatPromptTemplate.from_messages([("system", self.prompt_template), ("human", "{source_text}")])
            if ChatPromptTemplate
            else None
        )

    def run(self, source_text: str, *, platform: str, context: AIExecutionContext | None = None) -> ParseResult:
        del context
        summary = source_text.strip()[:120] or "No source text provided."
        return ParseResult(
            platform=platform,
            summary=summary,
            selling_points=["场景", "利益点", "证据"],
            detected_assets=["cover_candidate", "cta_candidate"],
        )
