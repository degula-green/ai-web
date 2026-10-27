from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from app.api.deps import get_current_auth_context, get_data_collection_service
from app.core.contract import contract_success
from app.services.data_collection_service import DataCollectionService

router = APIRouter()


@router.get("/overview")
def get_overview(
    service: DataCollectionService = Depends(get_data_collection_service),
    context=Depends(get_current_auth_context),
):
    data = service.get_overview(owner_user_id=context.user.id)
    return contract_success(data, msg="success")


@router.get("/platforms")
def get_platforms(
    service: DataCollectionService = Depends(get_data_collection_service),
    context=Depends(get_current_auth_context),
):
    data = service.get_platforms(owner_user_id=context.user.id)
    return contract_success(data, msg="success")


@router.get("/platforms/{platformCode}")
def get_platform_detail(
    platformCode: str,
    service: DataCollectionService = Depends(get_data_collection_service),
    context=Depends(get_current_auth_context),
):
    data = service.get_platform_detail(owner_user_id=context.user.id, platform_code=platformCode)
    return contract_success(data, msg="success")


@router.get("/platforms/{platformCode}/hot-ranks")
async def get_hot_ranks(
    background_tasks: BackgroundTasks,
    platformCode: str,
    snapshot_no: str | None = Query(default=None, alias="snapshotNo"),
    board_type: str | None = Query(default=None, alias="boardType"),
    sort_by: str = Query(default="heat", alias="sortBy"),
    page_no: int = Query(default=1, ge=1, alias="pageNo"),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    force: bool = Query(default=False),
    service: DataCollectionService = Depends(get_data_collection_service),
    context=Depends(get_current_auth_context),
):
    data = await service.get_hot_ranks(
        owner_user_id=context.user.id,
        platform_code=platformCode,
        snapshot_no=snapshot_no,
        board_type=board_type,
        sort_by=sort_by,
        page_no=page_no,
        page_size=page_size,
        force=force,
        background_tasks=background_tasks,
    )
    return contract_success(data, msg="success")


@router.get("/proxy-download")
async def proxy_download(
    url: str,
    title: str | None = Query(default=None),
    service: DataCollectionService = Depends(get_data_collection_service),
):
    return await service.get_proxy_download_response(url=url, title=title)


@router.get("/staged-results/{taskId}")
async def get_staged_results(
    taskId: str,
    service: DataCollectionService = Depends(get_data_collection_service),
    context=Depends(get_current_auth_context),
):
    """查看采集任务暂存在 Redis 中的数据"""
    data = await service.get_staged_results(task_id=taskId)
    return contract_success(data, msg="success")


@router.post("/collect")
async def collect_content(
    payload: dict,
    service: DataCollectionService = Depends(get_data_collection_service),
    context=Depends(get_current_auth_context),
):
    """将选中的内容入库并建立关联"""
    task_id = payload.get("taskId")
    platform = payload.get("platform")
    selected_ids = payload.get("selectedIds", [])

    count = await service.collect_staged_content(
        user_id=context.user.id,
        task_id=task_id,
        platform=platform,
        selected_ids=selected_ids
    )
    return contract_success({"collectedCount": count}, msg="success")


@router.post("/collect-detail-url")
async def collect_detail_url(
    payload: dict,
    service: DataCollectionService = Depends(get_data_collection_service),
    context=Depends(get_current_auth_context),
):
    """detail 链接采集完成后，按链接内容 ID 建立当前用户素材关系。"""
    data = await service.collect_detail_url_result(
        user_id=context.user.id,
        task_id=str(payload.get("taskId") or ""),
        platform=str(payload.get("platform") or "douyin"),
        url=str(payload.get("url") or ""),
    )
    return contract_success(data, msg="success")


@router.get("/my-content")
async def get_my_content(
    platform: str = Query(..., description="平台标识"),
    contentKind: str | None = Query(None, description="内容类型: image/video"),
    service: DataCollectionService = Depends(get_data_collection_service),
    context=Depends(get_current_auth_context),
):
    """查看我的内容"""
    data = await service.get_my_content(
        user_id=context.user.id,
        platform=platform,
        content_kind=contentKind
    )
    return contract_success(data, msg="success")


@router.delete("/users/me/material-relations/{chainId}")
async def delete_material_relation(
    chainId: str,
    service: DataCollectionService = Depends(get_data_collection_service),
    context=Depends(get_current_auth_context),
):
    """从当前用户素材库移除内容。只删除用户关联，不删除平台内容主表。"""
    deleted = await service.delete_material_relation(user_id=context.user.id, chain_id=chainId)
    return contract_success({"deleted": deleted, "chainId": chainId}, msg="success")


@router.get("/contents/{contentId}")
async def get_content_detail(
    contentId: str,
    platformCode: str = Query(..., alias="platformCode"),
    contentKind: str = Query(..., alias="contentKind"),
    sourceScene: str | None = Query(None, alias="sourceScene"),
    sourceRefNo: str | None = Query(None, alias="sourceRefNo"),
    service: DataCollectionService = Depends(get_data_collection_service),
    context=Depends(get_current_auth_context),
):
    """查看内容详情（采集预览或我的素材）"""
    data = await service.get_content_detail(
        content_id=contentId,
        platform_code=platformCode,
        content_kind=contentKind,
        source_scene=sourceScene,
        source_ref_no=sourceRefNo,
    )
    return contract_success(data, msg="success")
