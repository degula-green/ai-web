from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_background_asset_service, get_current_auth_context
from app.core.response import ResponseEnvelope, success_response
from app.schemas.background_asset import (
    BackgroundAssetCreateRequest,
    BackgroundAssetListResponse,
    BackgroundAssetRead,
)
from app.services.auth_service import AuthContext
from app.services.background_asset_service import BackgroundAssetService

router = APIRouter()


@router.get("", response_model=ResponseEnvelope[BackgroundAssetListResponse])
def list_background_assets(
    media_type: str | None = Query(default=None),
    context: AuthContext = Depends(get_current_auth_context),
    service: BackgroundAssetService = Depends(get_background_asset_service),
) -> ResponseEnvelope[BackgroundAssetListResponse]:
    data = service.list_available(user_id=context.user.id, media_type=media_type)
    return success_response(data)


@router.post("", response_model=ResponseEnvelope[BackgroundAssetRead])
def create_background_asset(
    payload: BackgroundAssetCreateRequest,
    context: AuthContext = Depends(get_current_auth_context),
    service: BackgroundAssetService = Depends(get_background_asset_service),
) -> ResponseEnvelope[BackgroundAssetRead]:
    data = service.create_user_asset(user_id=context.user.id, payload=payload)
    return success_response(data, message="background asset created")


@router.delete("/{asset_id}", response_model=ResponseEnvelope[dict])
def delete_background_asset(
    asset_id: int,
    context: AuthContext = Depends(get_current_auth_context),
    service: BackgroundAssetService = Depends(get_background_asset_service),
) -> ResponseEnvelope[dict]:
    service.delete_user_asset(user_id=context.user.id, asset_id=asset_id)
    return success_response({"asset_id": asset_id}, message="background asset deleted")
