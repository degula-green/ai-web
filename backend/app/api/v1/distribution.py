from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_auth_context, get_distribution_service, get_publish_plan_service
from app.core.response import ResponseEnvelope, success_response
from app.schemas.distribution import (
    DistributionContentListResponse,
    DistributionPublishRequest,
    DistributionPublishResult,
    DistributionRequest,
    DistributionResult,
    PublishPlanOverviewResponse,
)
from app.services.auth_service import AuthContext
from app.services.distribution_service import DistributionService
from app.services.publish_plan_service import PublishPlanService

router = APIRouter()


@router.post("/dispatch", response_model=ResponseEnvelope[DistributionResult])
def dispatch_distribution(
    payload: DistributionRequest,
    service: DistributionService = Depends(get_distribution_service),
) -> ResponseEnvelope[DistributionResult]:
    return success_response(service.dispatch(payload))


@router.post("/publish", response_model=ResponseEnvelope[DistributionPublishResult])
def publish_distribution(
    payload: DistributionPublishRequest,
    context: AuthContext = Depends(get_current_auth_context),
    service: DistributionService = Depends(get_distribution_service),
) -> ResponseEnvelope[DistributionPublishResult]:
    return success_response(
        service.publish_for_user(user_id=context.user.id, payload=payload),
        message="发送成功",
    )


@router.get("/items", response_model=ResponseEnvelope[DistributionContentListResponse])
async def get_distribution_items(
    platformCode: str | None = Query(default=None),
    status: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    context: AuthContext = Depends(get_current_auth_context),
    service: DistributionService = Depends(get_distribution_service),
) -> ResponseEnvelope[DistributionContentListResponse]:
    return success_response(
        await service.list_content_items(
            user_id=context.user.id,
            platform_code=platformCode,
            content_status=status,
            keyword=keyword,
        )
    )


@router.get("/plans/overview", response_model=ResponseEnvelope[PublishPlanOverviewResponse])
def get_publish_plan_overview(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    context: AuthContext = Depends(get_current_auth_context),
    service: PublishPlanService = Depends(get_publish_plan_service),
) -> ResponseEnvelope[PublishPlanOverviewResponse]:
    return success_response(service.get_overview(user_id=context.user.id, month=month))
