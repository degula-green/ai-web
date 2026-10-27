from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_parse_service
from app.core.response import ResponseEnvelope, success_response
from app.schemas.parse import ParsePreviewRequest, ParseResult
from app.services.parse_service import ParseService

router = APIRouter()


@router.post("/preview", response_model=ResponseEnvelope[ParseResult])
def preview_parse(
    payload: ParsePreviewRequest,
    service: ParseService = Depends(get_parse_service),
) -> ResponseEnvelope[ParseResult]:
    return success_response(service.preview(payload))
