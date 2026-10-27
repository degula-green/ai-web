from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_workflow_service
from app.core.response import ResponseEnvelope, success_response
from app.schemas.workflow import WorkflowBlueprint
from app.services.workflow_service import WorkflowService

router = APIRouter()


@router.get("/blueprint", response_model=ResponseEnvelope[WorkflowBlueprint])
def get_workflow_blueprint(
    service: WorkflowService = Depends(get_workflow_service),
) -> ResponseEnvelope[WorkflowBlueprint]:
    return success_response(service.default_blueprint())
