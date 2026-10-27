from __future__ import annotations

from pathlib import Path

from app.schemas.review import ReviewResult

try:
    from langchain_core.prompts import ChatPromptTemplate
except ImportError:  # pragma: no cover - optional dependency in MVP environment
    ChatPromptTemplate = None


PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "review" / "review_prompt.md"


class ReviewChain:
    def __init__(self) -> None:
        self.prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
        self.langchain_prompt = (
            ChatPromptTemplate.from_messages([("system", self.prompt_template), ("human", "{content}")])
            if ChatPromptTemplate
            else None
        )

    def run(self, content: str) -> ReviewResult:
        approved = len(content.strip()) >= 20
        reasons = ["内容长度达标" if approved else "内容过短，需要补充平台卖点和结构化信息"]
        return ReviewResult(approved=approved, score=0.92 if approved else 0.48, reasons=reasons)
