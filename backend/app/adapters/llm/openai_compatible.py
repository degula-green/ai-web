from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.adapters.llm.base import BaseLLMProvider
from app.core.config import LLMSettings


class OpenAICompatibleLLMProvider(BaseLLMProvider):
    def __init__(self, settings: LLMSettings) -> None:
        self.settings = settings

    def complete(self, prompt: str) -> str:
        if not self.settings.api_key:
            return f"[stub:{self.settings.provider}/{self.settings.model}]"
        endpoint = self.settings.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.settings.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a precise marketing video script planner. Return exactly what the user asks for.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        }
        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.settings.api_key}",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.settings.timeout) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"LLM request failed: {exc.code} {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"LLM request failed: {exc.reason}") from exc

        data = json.loads(raw)
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("LLM response missing choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                    text_parts.append(item["text"])
            if text_parts:
                return "\n".join(text_parts)
        raise RuntimeError("LLM response missing content")
