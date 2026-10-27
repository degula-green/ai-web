from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_generation_service
from app.core.response import ResponseEnvelope, success_response
from app.schemas.generate import GeneratePreviewRequest, GenerateResult
from app.services.generation_service import GenerationService

router = APIRouter()


@router.post("/preview", response_model=ResponseEnvelope[GenerateResult])
def preview_generation(
    payload: GeneratePreviewRequest,
    service: GenerationService = Depends(get_generation_service),
) -> ResponseEnvelope[GenerateResult]:
    return success_response(service.preview(payload))
