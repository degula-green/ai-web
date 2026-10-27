from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_auth_context, get_upload_service
from app.core.response import ResponseEnvelope, success_response
from app.schemas.upload import AssetUploadTicketRead, AssetUploadTicketRequest
from app.services.auth_service import AuthContext
from app.services.upload_service import UploadService

router = APIRouter()


@router.post("/ticket", response_model=ResponseEnvelope[AssetUploadTicketRead])
def create_upload_ticket(
    payload: AssetUploadTicketRequest,
    _: AuthContext = Depends(get_current_auth_context),
    service: UploadService = Depends(get_upload_service),
) -> ResponseEnvelope[AssetUploadTicketRead]:
    data = service.create_ticket(payload)
    return success_response(data, message="upload ticket created")
