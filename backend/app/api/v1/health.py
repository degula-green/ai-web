from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Request

from app.api.deps import get_container
from app.core.constants import APP_VERSION
from app.core.response import ResponseEnvelope, success_response
from app.schemas.common import HealthPayload

router = APIRouter()


@router.get("/health", response_model=ResponseEnvelope[HealthPayload])
def health_check(request: Request, container=Depends(get_container)) -> ResponseEnvelope[HealthPayload]:
    payload = HealthPayload(
        service=container.settings.app.name,
        env=container.settings.app.env,
        version=APP_VERSION,
        task_store_backend=container.settings.app.task_store_backend,
        integrations={
            "mysql": container.settings.mysql.host,
            "redis": f"{container.settings.redis.host}:{container.settings.redis.port}/{container.settings.redis.db}",
            "qdrant": f"{container.settings.qdrant.host}:{container.settings.qdrant.port}",
            "mediacrawler": json.dumps(container.media_crawler_service.status(), ensure_ascii=False),
            "mediacrawler_tasks": json.dumps(container.media_crawler_orchestrator.status(), ensure_ascii=False),
            "request_path": str(request.url.path),
        },
    )
    return success_response(payload)
