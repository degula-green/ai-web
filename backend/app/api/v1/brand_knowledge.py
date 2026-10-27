from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, File, Form, UploadFile, Query

from app.api.deps import get_brand_knowledge_service, get_current_auth_context
from app.core.contract import contract_success
from app.core.exceptions import ContractError
from app.schemas.brand_knowledge import (
    BrandProductUpsertRequest,
    BuildContextPayloadRequest,
    SellingPointsSaveRequest,
    VisualAssetUpdateRequest,
)
from app.services.brand_knowledge_service import BrandKnowledgeService

router = APIRouter()


@router.get("/products")
def list_brand_products(
    keyword: str | None = Query(default=None),
    page_no: int = Query(default=1, ge=1, alias="pageNo"),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    sort_by: str = Query(default="updatedAt", alias="sortBy"),
    service: BrandKnowledgeService = Depends(get_brand_knowledge_service),
    context=Depends(get_current_auth_context),
):
    data = service.list_products(
        owner_user_id=context.user.id,
        keyword=keyword,
        page_no=page_no,
        page_size=page_size,
        sort_by=sort_by,
    )
    return contract_success(data, msg="查询成功")


@router.post("/products")
def create_brand_product(
    payload: BrandProductUpsertRequest,
    service: BrandKnowledgeService = Depends(get_brand_knowledge_service),
    context=Depends(get_current_auth_context),
):
    data = service.create_product(
        owner_user_id=context.user.id,
        operator_id=context.user.id,
        payload=payload.model_dump(),
    )
    return contract_success(data, msg="创建成功")


@router.get("/products/{brandId}")
def get_brand_product_detail(
    brandId: int,
    service: BrandKnowledgeService = Depends(get_brand_knowledge_service),
    context=Depends(get_current_auth_context),
):
    data = service.get_product_detail(owner_user_id=context.user.id, brand_id=brandId)
    return contract_success(data, msg="查询成功")


@router.put("/products/{brandId}")
def update_brand_product(
    brandId: int,
    payload: BrandProductUpsertRequest,
    service: BrandKnowledgeService = Depends(get_brand_knowledge_service),
    context=Depends(get_current_auth_context),
):
    data = service.update_product(
        owner_user_id=context.user.id,
        brand_id=brandId,
        operator_id=context.user.id,
        payload=payload.model_dump(),
    )
    return contract_success(data, msg="保存成功")


@router.delete("/products/{brandId}")
def delete_brand_product(
    brandId: int,
    service: BrandKnowledgeService = Depends(get_brand_knowledge_service),
    context=Depends(get_current_auth_context),
):
    data = service.delete_product(owner_user_id=context.user.id, brand_id=brandId, operator_id=context.user.id)
    return contract_success(data, msg="删除成功")


@router.get("/products/{brandId}/selling-points")
def list_selling_points(
    brandId: int,
    point_type: str | None = Query(default=None, alias="type"),
    status: str | None = Query(default=None),
    page_no: int = Query(default=1, ge=1, alias="pageNo"),
    page_size: int = Query(default=100, ge=1, le=200, alias="pageSize"),
    service: BrandKnowledgeService = Depends(get_brand_knowledge_service),
    context=Depends(get_current_auth_context),
):
    data = service.list_selling_points(
        owner_user_id=context.user.id,
        brand_id=brandId,
        point_type=point_type,
        status=status,
        page_no=page_no,
        page_size=page_size,
    )
    return contract_success(data, msg="查询成功")


@router.put("/products/{brandId}/selling-points")
def save_selling_points(
    brandId: int,
    payload: SellingPointsSaveRequest,
    service: BrandKnowledgeService = Depends(get_brand_knowledge_service),
    context=Depends(get_current_auth_context),
):
    data = service.save_selling_points(
        owner_user_id=context.user.id,
        brand_id=brandId,
        operator_id=context.user.id,
        upserts=[item.model_dump() for item in payload.upserts],
        delete_ids=payload.deleteIds,
    )
    return contract_success(data, msg="保存成功")


@router.get("/products/{brandId}/visual-assets")
def list_visual_assets(
    brandId: int,
    asset_type: str | None = Query(default=None, alias="assetType"),
    page_no: int = Query(default=1, ge=1, alias="pageNo"),
    page_size: int = Query(default=50, ge=1, le=100, alias="pageSize"),
    service: BrandKnowledgeService = Depends(get_brand_knowledge_service),
    context=Depends(get_current_auth_context),
):
    data = service.list_visual_assets(
        owner_user_id=context.user.id,
        brand_id=brandId,
        asset_type=asset_type,
        page_no=page_no,
        page_size=page_size,
    )
    return contract_success(data, msg="查询成功")


@router.post("/products/{brandId}/visual-assets/upload")
async def upload_visual_asset(
    brandId: int,
    file: UploadFile = File(...),
    assetType: str = Form(...),
    tags: str | None = Form(default=None),
    platforms: str | None = Form(default=None),
    scenarios: str | None = Form(default=None),
    relatedSellingPointIds: str | None = Form(default=None),
    usableForCover: bool = Form(default=False),
    usableForVideo: bool = Form(default=False),
    service: BrandKnowledgeService = Depends(get_brand_knowledge_service),
    context=Depends(get_current_auth_context),
):
    data = service.upload_visual_asset(
        owner_user_id=context.user.id,
        brand_id=brandId,
        operator_id=context.user.id,
        filename=file.filename or "asset.bin",
        content_type=file.content_type or "application/octet-stream",
        file_bytes=await file.read(),
        asset_type=assetType,
        tags=_parse_json_string_array(tags),
        platforms=_parse_json_string_array(platforms),
        scenarios=_parse_json_string_array(scenarios),
        related_selling_point_ids=_parse_json_string_array(relatedSellingPointIds),
        usable_for_cover=usableForCover,
        usable_for_video=usableForVideo,
    )
    return contract_success(data, msg="上传成功")


@router.put("/visual-assets/{assetId}")
def update_visual_asset(
    assetId: int,
    payload: VisualAssetUpdateRequest,
    service: BrandKnowledgeService = Depends(get_brand_knowledge_service),
    context=Depends(get_current_auth_context),
):
    data = service.update_visual_asset(
        owner_user_id=context.user.id,
        asset_id=assetId,
        operator_id=context.user.id,
        payload=payload.model_dump(exclude_unset=True),
    )
    return contract_success(data, msg="更新成功")


@router.delete("/visual-assets/{assetId}")
def delete_visual_asset(
    assetId: int,
    service: BrandKnowledgeService = Depends(get_brand_knowledge_service),
    context=Depends(get_current_auth_context),
):
    data = service.delete_visual_asset(
        owner_user_id=context.user.id,
        asset_id=assetId,
        operator_id=context.user.id,
    )
    return contract_success(data, msg="删除成功")


@router.post("/context/payload")
def build_context_payload(
    payload: BuildContextPayloadRequest,
    service: BrandKnowledgeService = Depends(get_brand_knowledge_service),
    context=Depends(get_current_auth_context),
):
    try:
        brand_id = int(payload.brandId)
    except ValueError as exc:
        raise ContractError("brandId 非法", status_code=400) from exc

    data = service.build_context_payload(
        owner_user_id=context.user.id,
        brand_id=brand_id,
        selling_point_ids=payload.sellingPointIds,
        asset_ids=payload.assetIds,
        tone_rules=payload.toneRules,
    )
    return contract_success(data, msg="组装成功")


def _parse_json_string_array(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    value = raw_value.strip()
    if not value:
        return []
    try:
        parsed: Any = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ContractError("JSON 参数格式错误", status_code=400) from exc
    if not isinstance(parsed, list):
        raise ContractError("参数必须是 JSON 数组", status_code=400)
    return [str(item) for item in parsed if str(item).strip()]
