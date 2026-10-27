from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_ai_model_service, get_current_auth_context
from app.core.contract import contract_success
from app.schemas.ai_model import (
    AIProviderTestRequest,
    AIProviderUpsertRequest,
    AITokenUsageLogCreateRequest,
)
from app.services.ai_model_service import AIModelService

router = APIRouter()


@router.post("/providers/test")
async def test_provider(
    payload: AIProviderTestRequest,
    service: AIModelService = Depends(get_ai_model_service),
    context=Depends(get_current_auth_context),
):
    _ = context
    result = await service.test_provider_connection(
        base_url=payload.baseUrl,
        api_key=payload.apiKey,
        model_name=payload.modelName,
        timeout_seconds=payload.timeoutSeconds,
    )
    return contract_success(
        {
            "ok": result.ok,
            "message": result.message,
            "latencyMs": result.latency_ms,
            "model": result.model,
        }
    )


@router.post("/providers")
async def upsert_provider(
    payload: AIProviderUpsertRequest,
    service: AIModelService = Depends(get_ai_model_service),
    context=Depends(get_current_auth_context),
):
    provider_view, test_result = await service.upsert_provider_config(
        operator_user_id=context.user.id,
        provider_code=payload.providerCode,
        provider_name=payload.providerName,
        base_url=payload.baseUrl,
        api_key=payload.apiKey,
        default_model=payload.modelName,
        timeout_seconds=payload.timeoutSeconds,
        is_enabled=payload.isEnabled,
        extra_config=payload.extraConfig,
    )
    return contract_success(
        {
            "provider": provider_view.model_dump(),
            "test": test_result.model_dump(),
        },
        msg="模型配置已保存",
    )


@router.get("/providers")
async def list_providers(
    includeDisabled: bool = Query(default=True),
    service: AIModelService = Depends(get_ai_model_service),
    context=Depends(get_current_auth_context),
):
    _ = context
    rows = service.list_provider_configs(include_disabled=includeDisabled)
    return contract_success({"list": [item.model_dump() for item in rows], "total": len(rows)})


@router.post("/usage/log")
async def log_token_usage(
    payload: AITokenUsageLogCreateRequest,
    service: AIModelService = Depends(get_ai_model_service),
    context=Depends(get_current_auth_context),
):
    service.create_usage_log(user_id=context.user.id, payload=payload)
    return contract_success(None, msg="token 用量已记录")


@router.get("/usage/summary")
async def get_usage_summary(
    fromTime: datetime | None = Query(default=None),
    toTime: datetime | None = Query(default=None),
    service: AIModelService = Depends(get_ai_model_service),
    context=Depends(get_current_auth_context),
):
    summary = service.summarize_usage(user_id=context.user.id, from_time=fromTime, to_time=toTime)
    return contract_success(summary.model_dump())
