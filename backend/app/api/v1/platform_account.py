from __future__ import annotations

import io
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.api.deps import get_container, get_current_auth_context, get_platform_account_service
from app.core.contract import contract_success
from app.schemas.platform_account import CookieBridgeBindRequest, SyncAccountWorksRequest
from app.services.platform_account_service import PlatformAccountService

router = APIRouter()


def _resolve_cookie_bridge_extension_dir(root_dir: Path) -> Path:
    candidates = (
        root_dir / "cookie-bridge" / "extension",
        root_dir / "MediaCrawlerPro-CookieBridge" / "extension",
    )
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    return candidates[0]


@router.get("/cookie-bridge/accounts")
async def list_cookie_bridge_accounts(
    service: PlatformAccountService = Depends(get_platform_account_service),
    container=Depends(get_container),
    context=Depends(get_current_auth_context),
):
    _ = context
    bridge_url = container.settings.media_crawler.default_cookie_bridge_url
    data = await service.list_cookie_bridge_accounts(bridge_url)
    return contract_success(data)


@router.get("/cookie-bridge/extension/download")
async def download_cookie_bridge_extension(
    container=Depends(get_container),
    context=Depends(get_current_auth_context),
):
    _ = context
    root_dir = Path(container.settings.media_crawler.root_dir)
    extension_dir = _resolve_cookie_bridge_extension_dir(root_dir)
    if not extension_dir.exists() or not extension_dir.is_dir():
        raise HTTPException(status_code=404, detail="CookieBridge extension not found")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in extension_dir.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(extension_dir.parent).as_posix())
    buffer.seek(0)

    headers = {
        "Content-Disposition": 'attachment; filename="CookieBridge-extension.zip"',
    }
    return StreamingResponse(buffer, media_type="application/zip", headers=headers)


@router.post("/cookie-bridge/bind")
async def bind_cookie_bridge_client(
    payload: CookieBridgeBindRequest,
    service: PlatformAccountService = Depends(get_platform_account_service),
    container=Depends(get_container),
    context=Depends(get_current_auth_context),
):
    from app.db.session import build_session_factory

    factory = build_session_factory(container.settings)
    with factory() as db:
        data = await service.bind_cookie_bridge_client(
            db,
            owner_id=context.user.id,
            bridge_url=container.settings.media_crawler.default_cookie_bridge_url,
            platform_code=payload.platformCode,
            client_id=payload.clientId,
            set_default=payload.setDefault,
        )
        data["uploaderStorageState"] = await service.export_uploader_storage_state(
            db,
            owner_id=context.user.id,
            account_id=int(data["accountId"]),
            root_dir=container.publishing_runtime.runtime_root,
        )
        return contract_success(data, msg="CookieBridge 账号绑定成功")


@router.post("/accounts/{accountId}/export-uploader-state")
async def export_uploader_storage_state(
    accountId: int,
    service: PlatformAccountService = Depends(get_platform_account_service),
    container=Depends(get_container),
    context=Depends(get_current_auth_context),
):
    from app.db.session import build_session_factory

    factory = build_session_factory(container.settings)
    with factory() as db:
        data = await service.export_uploader_storage_state(
            db,
            owner_id=context.user.id,
            account_id=accountId,
            root_dir=container.publishing_runtime.runtime_root,
        )
        return contract_success(data, msg="上传器授权文件导出成功")


@router.get("/accounts")
async def list_accounts(
    platformCode: str | None = Query(None, alias="platformCode"),
    service: PlatformAccountService = Depends(get_platform_account_service),
    container=Depends(get_container),
    context=Depends(get_current_auth_context),
):
    from app.db.session import build_session_factory

    factory = build_session_factory(container.settings)
    with factory() as db:
        rows = await service.list_accounts(db, context.user.id, platformCode)
        return contract_success({"list": rows, "total": len(rows)})


@router.post("/accounts/{accountId}/sync-self-works")
async def sync_self_works(
    accountId: int,
    payload: SyncAccountWorksRequest,
    service: PlatformAccountService = Depends(get_platform_account_service),
    container=Depends(get_container),
    context=Depends(get_current_auth_context),
):
    from app.db.session import build_session_factory

    factory = build_session_factory(container.settings)
    with factory() as db:
        data = await service.sync_douyin_self_works(
            db,
            owner_id=context.user.id,
            account_id=accountId,
            crawler_api_base_url=container.settings.media_crawler.crawler_api_base_url,
            max_count=payload.maxCount,
        )
        return contract_success(data, msg="账号作品同步成功")


@router.delete("/accounts/{accountId}")
async def unbind_account(
    accountId: int,
    service: PlatformAccountService = Depends(get_platform_account_service),
    container=Depends(get_container),
    context=Depends(get_current_auth_context),
):
    from app.db.session import build_session_factory

    factory = build_session_factory(container.settings)
    with factory() as db:
        acc = await service.unbind_account(db, accountId, context.user.id)
        if not acc:
            raise HTTPException(status_code=404, detail="账号不存在")
        return contract_success({"accountId": acc.id, "unbindAt": acc.updated_at}, msg="解绑成功")


@router.get("/auth/history")
async def get_auth_history(
    service: PlatformAccountService = Depends(get_platform_account_service),
    container=Depends(get_container),
    context=Depends(get_current_auth_context),
):
    from app.db.session import build_session_factory

    factory = build_session_factory(container.settings)
    with factory() as db:
        history = await service.get_auth_history(db, context.user.id)
        return contract_success({"list": history, "total": len(history)})
