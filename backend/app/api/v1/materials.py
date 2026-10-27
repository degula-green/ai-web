from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_material_service
from app.core.response import ResponseEnvelope, success_response
from app.schemas.material import MaterialIngestRequest, MaterialRead
from app.services.material_service import MaterialService

router = APIRouter()


@router.post("/intake", response_model=ResponseEnvelope[MaterialRead])
def intake_material(
    payload: MaterialIngestRequest,
    service: MaterialService = Depends(get_material_service),
) -> ResponseEnvelope[MaterialRead]:
    return success_response(service.ingest(payload), message="material stored")
