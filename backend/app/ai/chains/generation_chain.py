from __future__ import annotations

from pathlib import Path

from app.ai.context.builder import AIExecutionContext
from app.schemas.generate import GenerateResult

try:
    from langchain_core.prompts import ChatPromptTemplate
except ImportError:  # pragma: no cover - optional dependency in MVP environment
    ChatPromptTemplate = None


PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "generation" / "generation_prompt.md"


class GenerationChain:
    def __init__(self) -> None:
        self.prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
        self.langchain_prompt = (
            ChatPromptTemplate.from_messages([("system", self.prompt_template), ("human", "{topic}")])
            if ChatPromptTemplate
            else None
        )

    def run(self, topic: str, *, route_label: str, context: AIExecutionContext) -> GenerateResult:
        knowledge_hint = ""
        if context.knowledge_hits:
            knowledge_hint = f" 参考知识：{context.knowledge_hits[0].get('title', 'seed')}"
        return GenerateResult(
            title=f"{topic} 内容提纲",
            body=f"围绕 {topic} 输出首版脚本，突出卖点与平台适配。{knowledge_hint}".strip(),
            hashtags=["#内容自动化", "#AI工作流", "#抖音运营"],
            model_route=route_label,
        )
