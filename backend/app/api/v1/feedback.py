from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_feedback_service
from app.core.response import ResponseEnvelope, success_response
from app.schemas.feedback import FeedbackSummary
from app.services.feedback_service import FeedbackService

router = APIRouter()


@router.get("/{task_id}", response_model=ResponseEnvelope[FeedbackSummary])
def get_feedback_summary(
    task_id: str,
    service: FeedbackService = Depends(get_feedback_service),
) -> ResponseEnvelope[FeedbackSummary]:
    return success_response(service.get_summary(task_id))
