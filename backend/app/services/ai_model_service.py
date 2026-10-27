from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from app.core.exceptions import ContractError
from app.db.repositories.ai_model_repository import AIModelRepository, LLMConfigRecord
from app.schemas.ai_model import (
    AIProviderConfigView,
    AIProviderTestResult,
    AITokenUsageLogCreateRequest,
    AITokenUsageSummaryView,
)


@dataclass(slots=True)
class ProviderTestOutcome:
    ok: bool
    message: str
    latency_ms: int
    model: str


@dataclass(slots=True)
class LLMCompletionResult:
    config_name: str
    provider: str
    model_name: str
    content: str
    raw_response_text: str
    request_id: str | None


class AIModelService:
    def __init__(self, repository: AIModelRepository) -> None:
        self.repository = repository

    async def test_provider_connection(
        self,
        *,
        base_url: str,
        api_key: str,
        model_name: str,
        timeout_seconds: int,
    ) -> ProviderTestOutcome:
        started = time.perf_counter()
        endpoint = base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 8,
            "temperature": 0,
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
            latency = int((time.perf_counter() - started) * 1000)
            if response.status_code >= 400:
                body = response.text[:400]
                return ProviderTestOutcome(
                    ok=False,
                    message=f"HTTP {response.status_code}: {body}",
                    latency_ms=latency,
                    model=model_name,
                )
            return ProviderTestOutcome(ok=True, message="连接成功", latency_ms=latency, model=model_name)
        except Exception as exc:
            latency = int((time.perf_counter() - started) * 1000)
            return ProviderTestOutcome(ok=False, message=str(exc), latency_ms=latency, model=model_name)

    async def upsert_provider_config(
        self,
        *,
        operator_user_id: int,
        provider_code: str,
        provider_name: str,
        base_url: str,
        api_key: str,
        default_model: str,
        timeout_seconds: int,
        is_enabled: bool,
        extra_config: dict | None,
    ) -> tuple[AIProviderConfigView, AIProviderTestResult]:
        test_outcome = await self.test_provider_connection(
            base_url=base_url,
            api_key=api_key,
            model_name=default_model,
            timeout_seconds=timeout_seconds,
        )
        model = self.repository.upsert_provider_config(
            provider_code=provider_code,
            provider_name=provider_name,
            base_url=base_url,
            api_key=api_key,
            default_model=default_model,
            timeout_seconds=timeout_seconds,
            is_enabled=is_enabled,
            extra_config=extra_config,
            updated_by=operator_user_id,
            test_status="success" if test_outcome.ok else "failed",
            test_message=test_outcome.message[:500],
        )
        return self._to_provider_view(model), AIProviderTestResult(
            ok=test_outcome.ok,
            message=test_outcome.message,
            latencyMs=test_outcome.latency_ms,
            model=test_outcome.model,
        )

    def list_provider_configs(self, *, include_disabled: bool = True) -> list[AIProviderConfigView]:
        models = self.repository.list_provider_configs(include_disabled=include_disabled)
        return [self._to_provider_view(item) for item in models]

    def create_usage_log(self, *, user_id: int, payload: AITokenUsageLogCreateRequest) -> None:
        self.repository.create_usage_log(
            user_id=user_id,
            task_id=payload.taskId,
            scene=payload.scene,
            provider_code=payload.providerCode,
            model_name=payload.modelName,
            input_tokens=payload.inputTokens,
            output_tokens=payload.outputTokens,
            cached_tokens=payload.cachedTokens,
            estimated_cost=payload.estimatedCost,
            currency=payload.currency,
            request_id=payload.requestId,
            remark=payload.remark,
            metadata_json=payload.metadata,
        )

    def get_active_llm_config(self) -> LLMConfigRecord | None:
        return self.repository.get_active_llm_config()

    def complete_with_active_config(
        self,
        *,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> LLMCompletionResult:
        return self._complete_with_active_config(
            system_prompt="You are a precise product marketing video planner. Return exactly the structured result requested.",
            user_content=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def complete_with_active_config_multimodal(
        self,
        *,
        system_prompt: str,
        user_text: str,
        image_urls: list[str],
        temperature: float = 0.2,
        max_tokens: int = 4000,
    ) -> LLMCompletionResult:
        user_content: list[dict[str, Any]] = [{"type": "text", "text": user_text}]
        for raw_url in image_urls:
            url = str(raw_url or "").strip()
            if not url:
                continue
            user_content.append({"type": "image_url", "image_url": {"url": url}})
        return self._complete_with_active_config(
            system_prompt=system_prompt,
            user_content=user_content,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def _complete_with_active_config(
        self,
        *,
        system_prompt: str,
        user_content: str | list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
    ) -> LLMCompletionResult:
        config = self.repository.get_active_llm_config()
        if config is None:
            raise ContractError("AI???????????????? LLM ???", status_code=500)
        if not config.api_key:
            raise ContractError(f"AI??????????? `{config.config_name}` ??? API Key?", status_code=500)
        if not config.base_url:
            raise ContractError(f"AI??????????? `{config.config_name}` ??? base_url?", status_code=500)

        endpoint = config.base_url.rstrip("/") + "/chat/completions"
        payload: dict[str, object] = {
            "model": config.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": user_content},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if config.provider.lower() == "openai" and config.enable_thinking and config.reasoning_effort:
            payload["reasoning"] = {"effort": config.reasoning_effort}

        headers = {"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"}
        connect_timeout_seconds = 20.0
        write_timeout_seconds = 120.0
        pool_timeout_seconds = 120.0
        try:
            with httpx.Client(
                timeout=httpx.Timeout(
                    timeout=None,
                    connect=connect_timeout_seconds,
                    read=None,
                    write=write_timeout_seconds,
                    pool=pool_timeout_seconds,
                ),
            ) as client:
                response = client.post(endpoint, json=payload, headers=headers)
        except httpx.ConnectTimeout as exc:
            raise ContractError(
                f"AI????????????? `{config.config_name}` ?????connect_timeout={connect_timeout_seconds}??{exc}",
                status_code=502,
            ) from exc
        except httpx.WriteTimeout as exc:
            raise ContractError(
                f"AI????????????? `{config.config_name}` ???????write_timeout={write_timeout_seconds}??{exc}",
                status_code=502,
            ) from exc
        except Exception as exc:
            raise ContractError(
                f"AI????????????? `{config.config_name}` ???{exc}",
                status_code=502,
            ) from exc

        raw_text = response.text
        if response.status_code >= 400:
            raise ContractError(
                f"AI??????????? `{config.config_name}` ?? HTTP {response.status_code}?{raw_text[:500]}",
                status_code=502,
            )
        try:
            data = response.json()
        except Exception as exc:
            raise ContractError(
                f"AI??????????? `{config.config_name}` ????? JSON ???",
                status_code=502,
            ) from exc

        choices = data.get("choices") or []
        if not choices:
            raise ContractError(
                f"AI??????????? `{config.config_name}` ???? choices?",
                status_code=502,
            )
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            parsed_content = content
        elif isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                    text_parts.append(item["text"])
            parsed_content = "\n".join(text_parts).strip()
        else:
            parsed_content = ""
        if not parsed_content:
            raise ContractError(
                f"AI??????????? `{config.config_name}` ???????",
                status_code=502,
            )

        request_id = response.headers.get("x-request-id")
        if not request_id and isinstance(data, dict):
            request_id = str(data.get("request_id") or data.get("id") or "") or None

        return LLMCompletionResult(
            config_name=config.config_name,
            provider=config.provider,
            model_name=config.model_name,
            content=parsed_content,
            raw_response_text=json.dumps(data, ensure_ascii=False)[:4000],
            request_id=request_id,
        )

    def summarize_usage(
        self,
        *,
        user_id: int,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
    ) -> AITokenUsageSummaryView:
        summary = self.repository.summarize_usage(user_id=user_id, from_time=from_time, to_time=to_time)
        return AITokenUsageSummaryView(
            userId=user_id,
            inputTokens=summary.input_tokens,
            outputTokens=summary.output_tokens,
            cachedTokens=summary.cached_tokens,
            totalTokens=summary.total_tokens,
            estimatedCost=summary.estimated_cost,
            records=summary.records,
        )

    @staticmethod
    def _to_provider_view(model) -> AIProviderConfigView:
        return AIProviderConfigView(
            id=model.id,
            providerCode=model.provider_code,
            providerName=model.provider_name,
            baseUrl=model.base_url,
            defaultModel=model.default_model,
            isEnabled=bool(model.is_enabled),
            timeoutSeconds=model.timeout_seconds,
            lastTestStatus=model.last_test_status,
            lastTestMessage=model.last_test_message,
            lastTestAt=model.last_test_at,
            createdAt=model.created_at,
            updatedAt=model.updated_at,
        )
