from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import httpx
from sqlalchemy.exc import IntegrityError
from sqlalchemy import bindparam, or_, text
from sqlalchemy.orm import Session

from app.adapters.platforms.manager import PlatformAuthManager
from app.core.exceptions import ContractError
from app.db.models.platform_account import (
    CrawlerCookieAccountBinding,
    PlatformAccount,
    PlatformAccountAuthLog,
    PlatformAccountSession,
    PlatformCookieBridgeBinding,
)
from app.db.models.platform_account_content import PlatformAccountContent
from app.db.models.user_content import UserContentRelation
logger = logging.getLogger(__name__)


class PlatformAccountService:
    def __init__(self) -> None:
        pass

    async def list_cookie_bridge_accounts(self, bridge_url: str) -> dict[str, Any]:
        payload = await self._bridge_get(bridge_url, "/api/accounts")
        accounts = payload.get("accounts") or []
        return {
            "list": [
                {
                    "clientId": str(item.get("client_id") or ""),
                    "connected": bool(item.get("connected")),
                    "nicknames": item.get("nicknames") if isinstance(item.get("nicknames"), dict) else {},
                    "platforms": item.get("platforms") if isinstance(item.get("platforms"), dict) else {},
                    "connectedAt": item.get("connected_at"),
                    "lastSeen": item.get("last_seen"),
                }
                for item in accounts
                if item.get("client_id")
            ],
            "total": int(payload.get("total") or len(accounts)),
            "bridgeUrl": bridge_url.rstrip("/"),
        }

    async def bind_cookie_bridge_client(
        self,
        db: Session,
        *,
        owner_id: int,
        bridge_url: str,
        platform_code: str,
        client_id: str,
        set_default: bool = True,
    ) -> dict[str, Any]:
        platform_code = self._normalize_main_platform(platform_code)
        bridge_platform = self._to_bridge_platform(platform_code)
        client_id = self._safe_str(client_id)
        if not client_id:
            raise ContractError("CookieBridge client_id 不能为空", status_code=400)

        accounts_payload = await self._bridge_get(bridge_url, "/api/accounts")
        bridge_client = self._find_bridge_client(accounts_payload.get("accounts") or [], client_id)
        if not bridge_client:
            raise ContractError("CookieBridge 客户端未连接，请先启动插件并刷新", status_code=404)

        platform_info = (bridge_client.get("platforms") or {}).get(bridge_platform) or {}
        if not platform_info.get("has_cookies"):
            raise ContractError("该 CookieBridge 客户端没有当前平台 Cookie，请先在浏览器登录平台", status_code=400)

        cookie_payload = await self._bridge_get(
            bridge_url,
            f"/api/cookies/{bridge_platform}",
            params={"client_id": client_id},
        )
        cookie_string = self._safe_str(cookie_payload.get("cookies"))
        if not cookie_string:
            raise ContractError("CookieBridge 未返回 Cookie，请确认插件连接和登录状态", status_code=400)

        now = datetime.now()
        cookies = self._normalize_bridge_cookie_items(
            cookie_payload.get("cookies_raw"),
            cookie_string=cookie_string,
            platform=bridge_platform,
        )
        local_storage = self._normalize_bridge_local_storage(cookie_payload.get("local_storage"))
        local_identity_snapshot = (
            self._extract_douyin_local_identity_snapshot(local_storage)
            if platform_code == "douyin"
            else {}
        )
        (
            remote_identity_snapshot,
            identity_verified,
            identity_verification_source,
        ) = await self._fetch_bridge_identity_snapshot(
            platform_code=platform_code,
            cookies=cookies,
        )
        merged_identity_snapshot = self._merge_identity_snapshots(
            local_snapshot=local_identity_snapshot,
            remote_snapshot=remote_identity_snapshot,
        )
        if platform_code == "bilibili" and not identity_verified:
            raise ContractError("B站登录态校验未通过，请重新登录后再绑定", status_code=400)
        nicknames = bridge_client.get("nicknames") if isinstance(bridge_client.get("nicknames"), dict) else {}
        account_name = (
            self._normalize_identity(merged_identity_snapshot.get("account_name"))
            or self._normalize_identity(merged_identity_snapshot.get("unique_id"))
            or self._normalize_identity(merged_identity_snapshot.get("short_id"))
            or self._normalize_identity(merged_identity_snapshot.get("nickname"))
            or self._safe_str(nicknames.get(bridge_platform))
            or (
            f"{self._display_main_platform_name(platform_code)}已登录账号"
        ))
        identity_fallback, identity_source = self._extract_identity_fallback(
            account_info=merged_identity_snapshot,
            cookies=cookies,
        )
        identity_profile = self._build_identity_profile(
            account_info=merged_identity_snapshot,
            cookies=cookies,
            local_storage=local_storage,
        )
        cookie_hash = self._hash_json_payload(cookies)
        storage_hash = self._hash_json_payload(local_storage)

        binding = (
            db.query(PlatformCookieBridgeBinding)
            .filter(
                PlatformCookieBridgeBinding.owner_user_id == owner_id,
                PlatformCookieBridgeBinding.platform_code == platform_code,
                PlatformCookieBridgeBinding.bridge_client_id == client_id,
            )
            .first()
        )

        account: PlatformAccount | None = None
        if binding and binding.platform_account_id:
            account = db.query(PlatformAccount).filter(PlatformAccount.id == binding.platform_account_id).first()
            if account and identity_profile["identity_value"]:
                existing_identity = self._normalize_identity(account.identity_value or account.sec_user_id or account.platform_uid)
                incoming_identity = self._normalize_identity(identity_profile["identity_value"])
                if existing_identity and incoming_identity and existing_identity != incoming_identity:
                    account.account_status = "account_mismatch"
                    account.last_identity_error = "cookie bridge client reported a different account identity"
                    account = None

        if not account and identity_profile["identity_value"]:
            account = (
                db.query(PlatformAccount)
                .filter(
                    PlatformAccount.owner_user_id == owner_id,
                    PlatformAccount.platform_code == platform_code,
                    PlatformAccount.identity_value == identity_profile["identity_value"],
                )
                .first()
            )

        if not account and identity_profile["platform_uid"]:
            account = (
                db.query(PlatformAccount)
                .filter(
                    PlatformAccount.owner_user_id == owner_id,
                    PlatformAccount.platform_code == platform_code,
                    PlatformAccount.platform_uid == identity_profile["platform_uid"],
                )
                .first()
            )

        if not account and identity_profile["sec_user_id"]:
            account = (
                db.query(PlatformAccount)
                .filter(
                    PlatformAccount.owner_user_id == owner_id,
                    PlatformAccount.platform_code == platform_code,
                    PlatformAccount.sec_user_id == identity_profile["sec_user_id"],
                )
                .first()
            )

        generic_account_name = f"{self._display_main_platform_name(platform_code)}已登录账号"
        is_generic_account_name = account_name == generic_account_name

        if not account:
            if not is_generic_account_name:
                account = (
                    db.query(PlatformAccount)
                    .filter(
                        PlatformAccount.owner_user_id == owner_id,
                        PlatformAccount.platform_code == platform_code,
                        PlatformAccount.is_deleted == 0,
                        PlatformAccount.account_name == account_name,
                    )
                    .first()
                )

        if not account and identity_profile["platform_uid"] and not is_generic_account_name:
            # Legacy CookieBridge rows were created before platforms such as
            # Bilibili persisted platform_uid. Reuse the same unbound row
            # instead of creating a duplicate account on refresh.
            account = (
                db.query(PlatformAccount)
                .filter(
                    PlatformAccount.owner_user_id == owner_id,
                    PlatformAccount.platform_code == platform_code,
                    PlatformAccount.is_deleted == 0,
                    PlatformAccount.platform_uid.is_(None),
                    or_(
                        PlatformAccount.account_name == account_name,
                        PlatformAccount.nickname == account_name,
                    ),
                )
                .first()
            )

        if not account:
            account = PlatformAccount(
                owner_user_id=owner_id,
                platform_code=platform_code,
                account_name=account_name,
                nickname=self._normalize_identity(merged_identity_snapshot.get("nickname")) or account_name,
                avatar_url=self._normalize_identity(merged_identity_snapshot.get("avatar_url")) or None,
                platform_uid=identity_profile["platform_uid"],
                identity_type=identity_profile["identity_type"],
                identity_value=identity_profile["identity_value"],
                sec_user_id=identity_profile["sec_user_id"],
                identity_fallback=identity_fallback or None,
                identity_source=identity_source or None,
                auth_status="authorized",
                account_status="active" if identity_profile["identity_value"] else "needs_rebind",
                last_identity_verified_at=now if identity_profile["identity_value"] else None,
                account_type="cookie_bridge",
            )
            db.add(account)
            try:
                db.flush()
            except IntegrityError as exc:
                db.rollback()
                account = (
                    db.query(PlatformAccount)
                    .filter(
                        PlatformAccount.owner_user_id == owner_id,
                        PlatformAccount.platform_code == platform_code,
                        PlatformAccount.platform_uid == identity_profile["platform_uid"],
                    )
                    .first()
                )
                if not account:
                    raise exc
                account.account_name = account_name
                account.nickname = self._normalize_identity(merged_identity_snapshot.get("nickname")) or account.nickname or account_name
                account.avatar_url = self._normalize_identity(merged_identity_snapshot.get("avatar_url")) or account.avatar_url
                account.platform_uid = identity_profile["platform_uid"] or account.platform_uid
                account.identity_type = identity_profile["identity_type"] or account.identity_type
                account.identity_value = identity_profile["identity_value"] or account.identity_value
                account.sec_user_id = identity_profile["sec_user_id"] or account.sec_user_id
                account.identity_fallback = identity_fallback or account.identity_fallback
                account.identity_source = identity_source or account.identity_source
                account.auth_status = "authorized"
                has_identity = bool(account.identity_value or account.sec_user_id or account.platform_uid)
                account_verified = identity_verified or platform_code != "bilibili"
                account.account_status = "active" if has_identity and account_verified else "needs_rebind"
                account.last_identity_verified_at = now if has_identity and account_verified else account.last_identity_verified_at
                account.last_identity_error = None
                account.account_type = account.account_type or "cookie_bridge"
                account.is_deleted = False
                account.updated_at = now
        else:
            account.account_name = account_name
            account.nickname = self._normalize_identity(merged_identity_snapshot.get("nickname")) or account.nickname or account_name
            account.avatar_url = self._normalize_identity(merged_identity_snapshot.get("avatar_url")) or account.avatar_url
            account.platform_uid = identity_profile["platform_uid"] or account.platform_uid
            account.identity_type = identity_profile["identity_type"] or account.identity_type
            account.identity_value = identity_profile["identity_value"] or account.identity_value
            account.sec_user_id = identity_profile["sec_user_id"] or account.sec_user_id
            account.identity_fallback = identity_fallback or account.identity_fallback
            account.identity_source = identity_source or account.identity_source
            account.auth_status = "authorized"
            has_identity = bool(account.identity_value or account.sec_user_id or account.platform_uid)
            account_verified = identity_verified or platform_code != "bilibili"
            account.account_status = "active" if has_identity and account_verified else "needs_rebind"
            account.last_identity_verified_at = now if has_identity and account_verified else account.last_identity_verified_at
            account.last_identity_error = None
            account.account_type = account.account_type or "cookie_bridge"
            account.is_deleted = False
            account.updated_at = now

        account.tags = self._merge_account_tags(
            existing_tags=account.tags,
            account_info={
                **merged_identity_snapshot,
                "bridge_client_id": client_id,
                "bridge_platform": bridge_platform,
            },
            identity_fallback=identity_fallback,
            identity_source=identity_source,
        )
        account.tags["bridgeClientId"] = client_id
        account.tags["bridgePlatform"] = bridge_platform

        session = db.query(PlatformAccountSession).filter(PlatformAccountSession.account_id == account.id).first()
        if not session:
            session = PlatformAccountSession(
                account_id=account.id,
                cookies=cookies,
                local_storage=local_storage,
                auth_type="cookie_bridge",
                cookie_blob=json.dumps(cookies, ensure_ascii=False, separators=(",", ":")),
                status="active",
                session_status="active",
                cookie_hash=cookie_hash,
                storage_hash=storage_hash,
                source_type="cookie_bridge",
                source_client_id=client_id,
                validated_identity=identity_profile["identity_value"],
                last_sync_at=now,
                last_validated_at=now,
                last_refresh_at=now,
                cookie_version=1,
            )
            db.add(session)
        else:
            session.cookies = cookies
            session.local_storage = local_storage
            session.auth_type = "cookie_bridge"
            session.cookie_blob = json.dumps(cookies, ensure_ascii=False, separators=(",", ":"))
            session.status = "active"
            session.session_status = "active"
            session.cookie_hash = cookie_hash
            session.storage_hash = storage_hash
            session.source_type = "cookie_bridge"
            session.source_client_id = client_id
            session.validated_identity = identity_profile["identity_value"]
            session.last_validation_error = None
            session.last_sync_at = now
            session.last_validated_at = now
            session.last_refresh_at = now
            session.cookie_version = int(session.cookie_version or 0) + 1

        crawler_cookie_account_id = self._upsert_crawler_cookie_account(
            db,
            account_name=account_name,
            platform_name=bridge_platform,
            cookie_string=cookie_string,
            existing_id=binding.crawler_cookie_account_id if binding else None,
        )

        if not binding:
            binding = PlatformCookieBridgeBinding(
                owner_user_id=owner_id,
                platform_code=platform_code,
                bridge_client_id=client_id,
            )
            db.add(binding)

        if set_default:
            db.query(PlatformCookieBridgeBinding).filter(
                PlatformCookieBridgeBinding.owner_user_id == owner_id,
                PlatformCookieBridgeBinding.platform_code == platform_code,
                PlatformCookieBridgeBinding.bridge_client_id != client_id,
            ).update({"is_default": False}, synchronize_session=False)

        binding.platform_account_id = account.id
        binding.crawler_cookie_account_id = crawler_cookie_account_id
        binding.status = "active"
        binding.is_default = bool(set_default)
        binding.last_reported_identity = identity_profile["identity_value"]
        binding.last_reported_nickname = self._normalize_identity(merged_identity_snapshot.get("nickname")) or account_name
        binding.last_cookie_hash = cookie_hash
        binding.last_sync_at = now

        self._upsert_crawler_cookie_binding(
            db,
            owner_id=owner_id,
            platform_code=platform_code,
            platform_account_id=account.id,
            crawler_cookie_account_id=crawler_cookie_account_id,
            is_default=set_default,
        )

        db.add(
            PlatformAccountAuthLog(
                account_id=account.id,
                event_type="bind" if session.cookie_version == 1 else "refresh",
                event_status="success",
                extra_data={
                    "authType": "cookie_bridge",
                    "bridgeClientId": client_id,
                    "bridgePlatform": bridge_platform,
                    "cookieSource": cookie_payload.get("source"),
                    "crawlerCookieAccountId": crawler_cookie_account_id,
                    "identityType": identity_profile["identity_type"] or None,
                    "identityValue": identity_profile["identity_value"] or None,
                    "identityVerified": identity_verified,
                    "identityVerificationSource": identity_verification_source or None,
                },
            )
        )

        db.commit()
        return {
            "accountId": int(account.id),
            "crawlerCookieAccountId": int(crawler_cookie_account_id),
            "bridgeClientId": client_id,
            "platformCode": platform_code,
            "syncedAt": now,
        }

    async def export_uploader_storage_state(
        self,
        db: Session,
        *,
        owner_id: int,
        account_id: int,
        root_dir: str | Path,
    ) -> dict[str, Any]:
        account = (
            db.query(PlatformAccount)
            .filter(
                PlatformAccount.id == account_id,
                PlatformAccount.owner_user_id == owner_id,
                PlatformAccount.is_deleted == 0,
            )
            .first()
        )
        if not account:
            raise ContractError("账号不存在", status_code=404)

        session = (
            db.query(PlatformAccountSession)
            .filter(PlatformAccountSession.account_id == account.id)
            .first()
        )
        if not session or not isinstance(session.cookies, list) or not session.cookies:
            raise ContractError("账号缺少可导出的会话数据", status_code=400)

        storage_state = self._build_uploader_storage_state(
            platform_code=account.platform_code,
            cookies=session.cookies,
            local_storage=session.local_storage,
        )
        target_path = self._resolve_uploader_cookie_file_path(root_dir=root_dir, account_id=account.id)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(
            json.dumps(storage_state, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        return {
            "accountId": int(account.id),
            "platformCode": account.platform_code,
            "fileName": target_path.name,
            "filePath": str(target_path),
            "originCount": len(storage_state.get("origins") or []),
            "cookieCount": len(storage_state.get("cookies") or []),
        }

    async def sync_douyin_self_works(
        self,
        db: Session,
        *,
        owner_id: int,
        account_id: int,
        crawler_api_base_url: str,
        max_count: int = 50,
    ) -> dict[str, Any]:
        account = (
            db.query(PlatformAccount)
            .filter(
                PlatformAccount.id == account_id,
                PlatformAccount.owner_user_id == owner_id,
                PlatformAccount.is_deleted == 0,
            )
            .first()
        )
        if not account:
            raise ContractError("账号不存在", status_code=404)
        if self._normalize_main_platform(account.platform_code) != "douyin":
            raise ContractError("仅支持抖音账号同步作品", status_code=400)

        session = (
            db.query(PlatformAccountSession)
            .filter(PlatformAccountSession.account_id == account.id)
            .first()
        )
        if not session or not isinstance(session.cookies, list) or not session.cookies:
            raise ContractError("账号缺少有效 Cookie 会话", status_code=400)

        sec_user_id = self._extract_douyin_sec_user_id(account=account, session=session)

        payload = {
            "account_id": int(account.id),
            "sec_user_id": sec_user_id,
            "cookies": session.cookies,
            "local_storage": session.local_storage,
            "user_agent": session.user_agent,
            "max_count": int(max_count),
            "account_name": account.account_name,
            "nickname": account.nickname,
        }

        sync_result = await self._crawler_post(
            crawler_api_base_url,
            "/douyin/self-sync",
            payload,
        )
        sync_status = str(sync_result.get("status") or "completed").strip() or "completed"
        sync_error = self._safe_str(sync_result.get("error")) or None
        aweme_ids = [
            str(item).strip()
            for item in (sync_result.get("aweme_ids") or [])
            if str(item).strip()
        ]

        relation_count = 0
        duplicated_count = 0
        for aweme_id in aweme_ids:
            created = self._ensure_user_content_relation(
                db,
                user_id=owner_id,
                platform="dy",
                relation_field="dy_aweme_id",
                content_id=aweme_id,
                task_id=f"platform_sync_account_{account.id}",
            )
            if created:
                relation_count += 1
            else:
                duplicated_count += 1

        session.last_sync_at = datetime.now()
        session.last_refresh_at = datetime.now()
        session.last_validated_at = datetime.now()
        db.commit()

        if sync_status == "completed":
            self._refresh_platform_account_contents(
                db,
                owner_id=owner_id,
                account=account,
                sec_user_id=str(sync_result.get("sec_user_id") or sec_user_id or "").strip(),
                aweme_ids=aweme_ids,
            )
            db.commit()

        return {
            "accountId": int(account.id),
            "platformCode": account.platform_code,
            "secUserId": str(sync_result.get("sec_user_id") or sec_user_id or ""),
            "status": sync_status,
            "syncedCount": int(sync_result.get("synced_count") or len(aweme_ids)),
            "relationCount": relation_count,
            "duplicatedCount": duplicated_count,
            "creatorSaved": bool(sync_result.get("creator_saved")),
            "awemeIds": aweme_ids,
            "error": sync_error,
        }

    async def list_accounts(self, db: Session, owner_id: int, platform_code: Optional[str] = None) -> list[dict[str, Any]]:
        query = db.query(PlatformAccount).filter(
            PlatformAccount.owner_user_id == owner_id,
            PlatformAccount.is_deleted == 0,
        )
        if platform_code:
            query = query.filter(PlatformAccount.platform_code == platform_code)

        accounts = query.order_by(PlatformAccount.updated_at.desc(), PlatformAccount.id.desc()).all()
        if not accounts:
            return []

        account_ids = [acc.id for acc in accounts]
        session_rows = (
            db.query(PlatformAccountSession)
            .filter(PlatformAccountSession.account_id.in_(account_ids))
            .all()
        )
        session_map = {row.account_id: row for row in session_rows}

        result: list[dict[str, Any]] = []
        for acc in accounts:
            sess = session_map.get(acc.id)
            result.append(
                {
                    "accountId": acc.id,
                    "platformCode": acc.platform_code,
                    "accountName": acc.account_name,
                    "nickname": acc.nickname,
                    "avatarUrl": acc.avatar_url,
                    "platformUid": acc.platform_uid,
                    "authStatus": acc.auth_status,
                    "accountStatus": acc.account_status,
                    "identityType": acc.identity_type,
                    "identityValue": acc.identity_value,
                    "secUserId": acc.sec_user_id,
                    "authType": sess.auth_type if sess else None,
                    "sessionStatus": (sess.session_status or sess.status) if sess else None,
                    "expiresAt": sess.expires_at if sess else None,
                    "lastSyncAt": sess.last_sync_at if sess else None,
                    "lastValidatedAt": sess.last_validated_at if sess else None,
                    "lastRefreshAt": sess.last_refresh_at if sess else None,
                    "lastIdentityVerifiedAt": acc.last_identity_verified_at,
                    "lastIdentityError": acc.last_identity_error,
                    "validatedIdentity": sess.validated_identity if sess else None,
                    "lastValidationError": sess.last_validation_error if sess else None,
                    "cookieVersion": sess.cookie_version if sess else None,
                    "updatedAt": acc.updated_at,
                }
            )
        return result

    async def unbind_account(self, db: Session, account_id: int, owner_id: int) -> Optional[PlatformAccount]:
        account = (
            db.query(PlatformAccount)
            .filter(
                PlatformAccount.id == account_id,
                PlatformAccount.owner_user_id == owner_id,
            )
            .first()
        )
        if not account:
            return None

        account.is_deleted = 1
        account.auth_status = "need_reauth"
        account.account_status = "disabled"
        account.last_identity_error = "account unbound"

        session = db.query(PlatformAccountSession).filter(PlatformAccountSession.account_id == account.id).first()
        if session:
            session.status = "revoked"
            session.session_status = "revoked"
            session.last_validation_error = "account unbound"
            session.last_validated_at = datetime.now()
            session.last_refresh_at = datetime.now()

        db.query(PlatformCookieBridgeBinding).filter(
            PlatformCookieBridgeBinding.owner_user_id == owner_id,
            PlatformCookieBridgeBinding.platform_account_id == account.id,
        ).update({"status": "disabled", "is_default": False}, synchronize_session=False)
        db.query(CrawlerCookieAccountBinding).filter(
            CrawlerCookieAccountBinding.owner_user_id == owner_id,
            CrawlerCookieAccountBinding.platform_account_id == account.id,
        ).update({"status": "disabled", "is_default": False}, synchronize_session=False)

        db.add(
            PlatformAccountAuthLog(
                account_id=account.id,
                event_type="revoke",
                event_status="success",
                extra_data={"sessionStatus": "revoked"},
            )
        )
        db.commit()
        return account

    async def get_auth_history(self, db: Session, owner_id: int, limit: int = 50) -> list[dict[str, Any]]:
        """Fetch platform authorization history for one owner."""
        logs = (
            db.query(PlatformAccountAuthLog, PlatformAccount.platform_code, PlatformAccount.account_name)
            .join(PlatformAccount, PlatformAccountAuthLog.account_id == PlatformAccount.id)
            .filter(PlatformAccount.owner_user_id == owner_id)
            .order_by(PlatformAccountAuthLog.created_at.desc())
            .limit(limit)
            .all()
        )

        result: list[dict[str, Any]] = []
        for log, p_code, acc_name in logs:
            result.append(
                {
                    "id": log.id,
                    "platformCode": p_code,
                    "accountName": acc_name,
                    "eventType": log.event_type,
                    "eventStatus": log.event_status,
                    "failReason": log.fail_reason,
                    "createdAt": log.created_at,
                    "extraData": log.extra_data,
                }
            )
        return result

    @staticmethod
    def _normalize_local_storage(raw_value: Any) -> dict[str, Any] | None:
        if raw_value is None:
            return None
        if isinstance(raw_value, dict):
            return raw_value
        if isinstance(raw_value, str):
            text = raw_value.strip()
            if not text:
                return None
            try:
                parsed = json.loads(text)
            except Exception:
                return {"_raw": text}
            if isinstance(parsed, dict):
                return parsed
            return {"_raw": text}
        return None

    @staticmethod
    def _build_cookie_blob(cookies: list[dict[str, Any]]) -> str | None:
        if not cookies:
            return None
        return json.dumps(cookies, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def _infer_cookie_expire_at(cookies: list[dict[str, Any]]) -> datetime | None:
        max_expire: float | None = None
        for item in cookies:
            if not isinstance(item, dict):
                continue
            raw_exp = item.get("expires", item.get("expiry"))
            try:
                exp_value = float(raw_exp)
            except (TypeError, ValueError):
                continue
            if exp_value <= 0:
                continue
            if max_expire is None or exp_value > max_expire:
                max_expire = exp_value

        if max_expire is None:
            return None

        try:
            return datetime.fromtimestamp(max_expire)
        except (TypeError, ValueError, OSError, OverflowError):
            return None

    @staticmethod
    def _safe_str(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @classmethod
    def _normalize_identity(cls, value: Any) -> str:
        text = cls._safe_str(value)
        if not text:
            return ""
        if text.lower() in {"self", "null", "undefined", "none", "nan", "{}", "[]"}:
            return ""
        return text

    @classmethod
    def _extract_identity_fallback(cls, *, account_info: dict[str, Any], cookies: list[dict[str, Any]]) -> tuple[str, str]:
        # If platform UID is missing, use a stable cookie identity key for dedupe/update.
        for key in ("uid", "sec_uid", "unique_id", "short_id"):
            value = cls._normalize_identity(account_info.get(key))
            if value:
                return value, f"account_info.{key}"

        cookie_map: dict[str, str] = {}
        for item in cookies:
            if not isinstance(item, dict):
                continue
            name = cls._safe_str(item.get("name")).lower()
            value = cls._normalize_identity(item.get("value"))
            if name and value:
                cookie_map[name] = value

        for name in ("uid_tt", "uid_tt_ss", "sessionid", "sessionid_ss", "x-web-secsdk-uid", "odin_tt", "ttwid", "dedeuserid"):
            value = cookie_map.get(name)
            if value:
                return value, f"cookie.{name}"

        return "", ""

    @classmethod
    def _merge_account_tags(
        cls,
        *,
        existing_tags: Any,
        account_info: dict[str, Any],
        identity_fallback: str,
        identity_source: str,
    ) -> dict[str, Any]:
        tags: dict[str, Any] = dict(existing_tags) if isinstance(existing_tags, dict) else {}
        if identity_fallback:
            tags["identityFallback"] = identity_fallback
        if identity_source:
            tags["identitySource"] = identity_source
        for key in ("sec_uid", "uid", "unique_id", "short_id"):
            value = cls._normalize_identity(account_info.get(key))
            if value:
                tags[key] = value
        return tags

    @classmethod
    def _build_identity_profile(
        cls,
        *,
        account_info: dict[str, Any],
        cookies: list[dict[str, Any]],
        local_storage: Any = None,
    ) -> dict[str, str | None]:
        local_snapshot = cls._extract_douyin_local_identity_snapshot(local_storage)
        sec_user_id = cls._normalize_identity(
            account_info.get("sec_uid")
            or account_info.get("secUserId")
            or account_info.get("sec_user_id")
            or local_snapshot.get("sec_uid")
            or local_snapshot.get("sec_user_id")
        )
        platform_uid = cls._normalize_identity(
            account_info.get("platform_uid")
            or account_info.get("uid")
            or account_info.get("user_id")
            or account_info.get("userId")
            or local_snapshot.get("uid")
            or local_snapshot.get("user_id")
        )
        identity_fallback, _ = cls._extract_identity_fallback(account_info=account_info, cookies=cookies)

        if sec_user_id:
            return {
                "identity_type": "sec_user_id",
                "identity_value": sec_user_id,
                "sec_user_id": sec_user_id,
                "platform_uid": platform_uid or sec_user_id,
            }
        if platform_uid:
            return {
                "identity_type": "platform_uid",
                "identity_value": platform_uid,
                "sec_user_id": None,
                "platform_uid": platform_uid,
            }
        if identity_fallback:
            return {
                "identity_type": "fallback",
                "identity_value": identity_fallback,
                "sec_user_id": None,
                "platform_uid": None,
            }
        return {
            "identity_type": None,
            "identity_value": None,
            "sec_user_id": None,
            "platform_uid": platform_uid or None,
        }

    @staticmethod
    def _hash_json_payload(payload: Any) -> str | None:
        if payload in (None, "", [], {}):
            return None
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    @staticmethod
    async def _bridge_get(bridge_url: str, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{bridge_url.rstrip('/')}{path}"
        try:
            async with httpx.AsyncClient(timeout=12.0, trust_env=False) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ContractError("CookieBridge 服务不可用，请确认 8274 服务和插件已启动", status_code=502) from exc

        data = response.json()
        if not data.get("isok"):
            raise ContractError(f"CookieBridge 返回错误: {data.get('msg') or '未知错误'}", status_code=400)
        payload = data.get("data")
        return payload if isinstance(payload, dict) else {}

    @classmethod
    async def _fetch_douyin_self_profile(cls, *, cookies: list[dict[str, Any]]) -> dict[str, Any]:
        cookie_header = cls._cookie_items_to_header(cookies)
        if not cookie_header:
            return {}
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.douyin.com/",
            "Origin": "https://www.douyin.com",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
            ),
            "Cookie": cookie_header,
        }
        try:
            async with httpx.AsyncClient(timeout=12.0, trust_env=False, follow_redirects=True) as client:
                response = await client.get("https://www.douyin.com/aweme/v1/web/query/user/", headers=headers)
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return {}
        return PlatformAuthManager._parse_douyin_profile_payload(payload)

    async def _fetch_bridge_identity_snapshot(
        self,
        *,
        platform_code: str,
        cookies: list[dict[str, Any]],
    ) -> tuple[dict[str, Any], bool, str]:
        """Validate the bridge login state and return a normalized identity snapshot."""
        if platform_code == "douyin":
            snapshot = await self._fetch_douyin_self_profile(cookies=cookies)
            return snapshot, bool(snapshot), "douyin.self_profile" if snapshot else ""
        if platform_code == "bilibili":
            snapshot = await self._fetch_bilibili_self_profile(cookies=cookies)
            return snapshot, True, "bilibili.nav"
        return {}, False, ""

    async def _fetch_bilibili_self_profile(self, *, cookies: list[dict[str, Any]]) -> dict[str, Any]:
        cookie_header = self._cookie_items_to_header(cookies)
        if not cookie_header:
            raise ContractError("B站登录态校验失败：Cookie 为空", status_code=400)
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.bilibili.com/",
            "Origin": "https://www.bilibili.com",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
            ),
            "Cookie": cookie_header,
        }
        try:
            async with httpx.AsyncClient(timeout=12.0, trust_env=False, follow_redirects=True) as client:
                response = await client.get(
                    "https://api.bilibili.com/x/web-interface/nav",
                    headers=headers,
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise ContractError("B站登录态校验请求失败，请稍后重试", status_code=502) from exc
        except ValueError as exc:
            raise ContractError("B站登录态校验返回了无效响应，请稍后重试", status_code=502) from exc
        return self._parse_bilibili_nav_payload(payload)

    @classmethod
    def _parse_bilibili_nav_payload(cls, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ContractError("B站登录态校验返回了无效响应，请稍后重试", status_code=502)
        code = payload.get("code")
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        if code != 0 or not data.get("isLogin"):
            message = cls._safe_str(payload.get("message")) or "账号未登录"
            raise ContractError(f"B站登录态已失效，请重新登录后再绑定：{message}", status_code=400)
        mid = cls._normalize_identity(data.get("mid"))
        if not mid:
            raise ContractError("B站登录态校验成功但未返回账号 UID", status_code=502)
        nickname = cls._normalize_identity(data.get("uname"))
        avatar_url = cls._normalize_identity(data.get("face"))
        if avatar_url.startswith("//"):
            avatar_url = f"https:{avatar_url}"
        return {
            "platform_uid": mid,
            "uid": mid,
            "user_id": mid,
            "nickname": nickname,
            "avatar_url": avatar_url,
            "account_name": nickname or mid,
        }

    @staticmethod
    def _cookie_items_to_header(cookies: list[dict[str, Any]] | None) -> str:
        parts: list[str] = []
        for item in cookies or []:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            value = str(item.get("value") or "").strip()
            if not name:
                continue
            parts.append(f"{name}={value}")
        return "; ".join(parts)

    @staticmethod
    def _find_bridge_client(accounts: list[Any], client_id: str) -> dict[str, Any] | None:
        for item in accounts:
            if isinstance(item, dict) and str(item.get("client_id") or "") == client_id:
                return item
        return None

    @classmethod
    def _cookie_string_to_items(cls, cookie_string: str, platform: str) -> list[dict[str, Any]]:
        domain = {
            "dy": ".douyin.com",
            "xhs": ".xiaohongshu.com",
            "ks": ".kuaishou.com",
            "bili": ".bilibili.com",
            "wb": ".weibo.com",
            "tieba": ".tieba.baidu.com",
            "zhihu": ".zhihu.com",
        }.get(platform, "")
        items: list[dict[str, Any]] = []
        for part in cookie_string.split(";"):
            if "=" not in part:
                continue
            name, value = part.split("=", 1)
            name = name.strip()
            value = value.strip()
            if not name:
                continue
            item: dict[str, Any] = {"name": name, "value": value}
            if domain:
                item["domain"] = domain
            items.append(item)
        return items

    @classmethod
    def _normalize_bridge_cookie_items(
        cls,
        raw_items: Any,
        *,
        cookie_string: str,
        platform: str,
    ) -> list[dict[str, Any]]:
        if isinstance(raw_items, list):
            normalized: list[dict[str, Any]] = []
            for raw in raw_items:
                if not isinstance(raw, dict):
                    continue
                name = cls._safe_str(raw.get("name"))
                if not name:
                    continue
                item: dict[str, Any] = {
                    "name": name,
                    "value": cls._safe_str(raw.get("value")),
                    "domain": cls._safe_str(raw.get("domain")),
                    "path": cls._safe_str(raw.get("path")) or "/",
                    "httpOnly": bool(raw.get("httpOnly")),
                    "secure": bool(raw.get("secure")),
                    "sameSite": cls._safe_str(raw.get("sameSite")) or "Lax",
                }
                raw_expires = raw.get("expires", raw.get("expiry"))
                try:
                    item["expires"] = float(raw_expires)
                except (TypeError, ValueError):
                    item["expires"] = -1
                normalized.append(item)
            if normalized:
                return normalized

        return cls._cookie_string_to_items(cookie_string, platform)

    @classmethod
    def _normalize_bridge_local_storage(cls, raw_value: Any) -> dict[str, Any] | None:
        normalized = cls._normalize_local_storage(raw_value)
        if not normalized:
            return None
        origins = normalized.get("origins")
        if not isinstance(origins, list):
            return None

        clean_origins: list[dict[str, Any]] = []
        for item in origins:
            if not isinstance(item, dict):
                continue
            origin = cls._safe_str(item.get("origin"))
            local_storage = item.get("localStorage")
            if not origin or not isinstance(local_storage, list):
                continue
            clean_entries: list[dict[str, str]] = []
            for entry in local_storage:
                if not isinstance(entry, dict):
                    continue
                key = cls._safe_str(entry.get("name"))
                if not key:
                    continue
                clean_entries.append(
                    {
                        "name": key,
                        "value": cls._safe_str(entry.get("value")),
                    }
                )
            clean_origins.append({"origin": origin, "localStorage": clean_entries})

        if not clean_origins:
            return None
        return {"origins": clean_origins}

    @classmethod
    def _build_uploader_storage_state(
        cls,
        *,
        platform_code: str,
        cookies: list[dict[str, Any]],
        local_storage: Any,
    ) -> dict[str, Any]:
        normalized_cookies = cls._normalize_bridge_cookie_items(
            cookies,
            cookie_string="",
            platform=cls._to_bridge_platform(platform_code),
        )
        normalized_local_storage = cls._normalize_bridge_local_storage(local_storage) or {"origins": []}
        return {
            "cookies": normalized_cookies,
            "origins": normalized_local_storage.get("origins") or [],
        }

    @staticmethod
    def _resolve_uploader_cookie_file_path(*, root_dir: str | Path, account_id: int) -> Path:
        base_dir = Path(root_dir)
        return base_dir / "cookiesFile" / f"platform_account_{int(account_id)}.json"

    @staticmethod
    def _normalize_main_platform(platform_code: str) -> str:
        key = str(platform_code or "").strip().lower()
        return {
            "dy": "douyin",
            "douyin": "douyin",
            "xhs": "xiaohongshu",
            "xiaohongshu": "xiaohongshu",
            "bili": "bilibili",
            "bilibili": "bilibili",
            "wb": "weibo",
            "weibo": "weibo",
            "ks": "kuaishou",
            "kuaishou": "kuaishou",
            "tieba": "tieba",
            "zhihu": "zhihu",
        }.get(key, key)

    @staticmethod
    def _to_bridge_platform(platform_code: str) -> str:
        key = str(platform_code or "").strip().lower()
        resolved = {
            "douyin": "dy",
            "dy": "dy",
            "xiaohongshu": "xhs",
            "xhs": "xhs",
            "bilibili": "bili",
            "bili": "bili",
            "weibo": "wb",
            "wb": "wb",
            "kuaishou": "ks",
            "ks": "ks",
            "tieba": "tieba",
            "zhihu": "zhihu",
        }.get(key)
        if not resolved:
            raise ContractError(f"CookieBridge 暂不支持平台: {platform_code}", status_code=400)
        return resolved

    @staticmethod
    def _display_main_platform_name(platform_code: str) -> str:
        key = str(platform_code or "").strip().lower()
        return {
            "douyin": "抖音",
            "dy": "抖音",
            "xiaohongshu": "小红书",
            "xhs": "小红书",
            "kuaishou": "快手",
            "ks": "快手",
            "bilibili": "B站",
            "bili": "B站",
            "weibo": "微博",
            "wb": "微博",
            "tieba": "贴吧",
            "zhihu": "知乎",
        }.get(key, platform_code)

    @staticmethod
    def _upsert_crawler_cookie_account(
        db: Session,
        *,
        account_name: str,
        platform_name: str,
        cookie_string: str,
        existing_id: int | None = None,
    ) -> int:
        if existing_id:
            result = db.execute(
                text(
                    """
                    UPDATE crawler_cookies_account
                    SET account_name = :account_name,
                        platform_name = :platform_name,
                        cookies = :cookies,
                        status = 0,
                        invalid_timestamp = 0,
                        update_time = CURRENT_TIMESTAMP
                    WHERE id = :account_id
                    """
                ),
                {
                    "account_id": int(existing_id),
                    "account_name": account_name,
                    "platform_name": platform_name,
                    "cookies": cookie_string,
                },
            )
            if int(getattr(result, "rowcount", 0) or 0) > 0:
                return int(existing_id)

        result = db.execute(
            text(
                """
                INSERT INTO crawler_cookies_account
                (account_name, platform_name, cookies, status, invalid_timestamp)
                VALUES (:account_name, :platform_name, :cookies, 0, 0)
                """
            ),
            {
                "account_name": account_name,
                "platform_name": platform_name,
                "cookies": cookie_string,
            },
        )
        return int(result.lastrowid)

    @staticmethod
    def _upsert_crawler_cookie_binding(
        db: Session,
        *,
        owner_id: int,
        platform_code: str,
        platform_account_id: int,
        crawler_cookie_account_id: int,
        is_default: bool,
    ) -> None:
        binding = (
            db.query(CrawlerCookieAccountBinding)
            .filter(
                CrawlerCookieAccountBinding.owner_user_id == owner_id,
                CrawlerCookieAccountBinding.platform_code == platform_code,
                CrawlerCookieAccountBinding.crawler_cookie_account_id == crawler_cookie_account_id,
            )
            .first()
        )
        if not binding:
            binding = CrawlerCookieAccountBinding(
                owner_user_id=owner_id,
                platform_code=platform_code,
                crawler_cookie_account_id=crawler_cookie_account_id,
            )
            db.add(binding)
        if is_default:
            db.query(CrawlerCookieAccountBinding).filter(
                CrawlerCookieAccountBinding.owner_user_id == owner_id,
                CrawlerCookieAccountBinding.platform_code == platform_code,
                CrawlerCookieAccountBinding.crawler_cookie_account_id != crawler_cookie_account_id,
            ).update({"is_default": False}, synchronize_session=False)
        binding.platform_account_id = platform_account_id
        binding.status = "active"
        binding.is_default = bool(is_default)
        binding.priority = 100

    @classmethod
    def _extract_douyin_sec_user_id(
        cls,
        *,
        account: PlatformAccount,
        session: PlatformAccountSession,
    ) -> str:
        candidates: list[Any] = []
        candidates.append(account.platform_uid)
        tags = account.tags if isinstance(account.tags, dict) else {}
        for key in ("sec_uid", "sec_user_id", "uid", "identityFallback"):
            candidates.append(tags.get(key))

        for value in candidates:
            sec_user_id = cls._match_sec_user_id(value)
            if sec_user_id:
                return sec_user_id

        for item in session.cookies or []:
            if not isinstance(item, dict):
                continue
            for key in ("name", "value", "domain", "path"):
                sec_user_id = cls._match_sec_user_id(item.get(key))
                if sec_user_id:
                    return sec_user_id

        for text in cls._iter_local_storage_texts(session.local_storage):
            sec_user_id = cls._match_sec_user_id(text)
            if sec_user_id:
                return sec_user_id
        return ""

    @classmethod
    def _iter_local_storage_texts(cls, local_storage: Any) -> list[str]:
        normalized = cls._normalize_bridge_local_storage(local_storage) or cls._normalize_local_storage(local_storage)
        if not isinstance(normalized, dict):
            return []
        origins = normalized.get("origins")
        if not isinstance(origins, list):
            return []
        texts: list[str] = []
        for origin_item in origins:
            if not isinstance(origin_item, dict):
                continue
            for entry in origin_item.get("localStorage") or []:
                if not isinstance(entry, dict):
                    continue
                value = cls._safe_str(entry.get("value"))
                if value:
                    texts.append(value)
        return texts

    @classmethod
    def _extract_douyin_local_identity_snapshot(cls, local_storage: Any) -> dict[str, str]:
        texts = cls._iter_local_storage_texts(local_storage)
        best_snapshot: dict[str, str] = {}
        best_score = -1
        for text in texts:
            parsed = None
            try:
                parsed = json.loads(text)
            except Exception:
                parsed = None

            candidates: list[dict[str, Any]] = []
            if isinstance(parsed, dict):
                candidates.append(parsed)
            elif isinstance(parsed, list):
                candidates.extend([item for item in parsed if isinstance(item, dict)])
            if not candidates:
                continue

            for candidate in candidates:
                sec_uid = cls._normalize_identity(
                    candidate.get("sec_uid")
                    or candidate.get("secUid")
                    or candidate.get("sec_user_id")
                    or candidate.get("secUserId")
                )
                uid = cls._normalize_identity(
                    candidate.get("uid")
                    or candidate.get("user_id")
                    or candidate.get("userId")
                )
                unique_id = cls._normalize_identity(candidate.get("unique_id") or candidate.get("uniqueId"))
                short_id = cls._normalize_identity(candidate.get("short_id") or candidate.get("shortId"))
                nickname = cls._normalize_identity(candidate.get("nickname") or candidate.get("nick_name"))
                avatar_url = cls._normalize_identity(
                    candidate.get("avatar_url")
                    or candidate.get("avatarUrl")
                    or candidate.get("avatar")
                )
                account_name = unique_id or short_id or nickname or sec_uid or uid
                if sec_uid or uid or unique_id or short_id or nickname:
                    snapshot = {
                        "sec_uid": sec_uid,
                        "sec_user_id": sec_uid,
                        "uid": uid,
                        "user_id": uid,
                        "unique_id": unique_id,
                        "short_id": short_id,
                        "nickname": nickname,
                        "avatar_url": avatar_url,
                        "account_name": account_name,
                    }
                    score = 0
                    if sec_uid:
                        score += 8
                    if nickname:
                        score += 4
                    if avatar_url:
                        score += 2
                    if unique_id or short_id:
                        score += 2
                    if uid:
                        score += 1
                    if score > best_score:
                        best_snapshot = snapshot
                        best_score = score
        return best_snapshot

    @classmethod
    def _merge_identity_snapshots(
        cls,
        *,
        local_snapshot: dict[str, Any],
        remote_snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        def pick(*values: Any) -> str:
            for value in values:
                normalized = cls._normalize_identity(value)
                if normalized:
                    return normalized
            return ""

        sec_uid = pick(
            local_snapshot.get("sec_uid"),
            local_snapshot.get("sec_user_id"),
            remote_snapshot.get("sec_uid"),
            remote_snapshot.get("sec_user_id"),
        )
        platform_uid = pick(
            sec_uid,
            remote_snapshot.get("platform_uid"),
            remote_snapshot.get("uid"),
            remote_snapshot.get("user_id"),
            remote_snapshot.get("userUid"),
            local_snapshot.get("uid"),
            local_snapshot.get("user_id"),
        )
        nickname = pick(local_snapshot.get("nickname"), remote_snapshot.get("nickname"))
        avatar_url = pick(local_snapshot.get("avatar_url"), remote_snapshot.get("avatar_url"))
        unique_id = pick(local_snapshot.get("unique_id"), remote_snapshot.get("unique_id"))
        short_id = pick(local_snapshot.get("short_id"), remote_snapshot.get("short_id"))
        account_name = pick(unique_id, short_id, nickname, sec_uid, platform_uid)
        return {
            "sec_uid": sec_uid,
            "sec_user_id": sec_uid,
            "uid": platform_uid,
            "user_id": platform_uid,
            "platform_uid": platform_uid,
            "nickname": nickname,
            "avatar_url": avatar_url,
            "unique_id": unique_id,
            "short_id": short_id,
            "account_name": account_name,
        }

    @staticmethod
    def _match_sec_user_id(value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        match = re.search(r"(MS4w[0-9A-Za-z_\-]+)", text)
        return match.group(1) if match else ""

    @staticmethod
    async def _crawler_post(base_url: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{base_url.rstrip('/')}{path}"
        try:
            async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip()
            raise ContractError(
                f"爬虫服务调用失败: {detail or exc.response.reason_phrase}",
                status_code=502,
            ) from exc
        except httpx.HTTPError as exc:
            raise ContractError("爬虫服务不可用，请确认 crawler-engine API 已启动", status_code=502) from exc

        data = response.json()
        if not isinstance(data, dict):
            raise ContractError("爬虫服务返回格式错误", status_code=502)
        return data

    def _refresh_platform_account_contents(
        self,
        db: Session,
        *,
        owner_id: int,
        account: PlatformAccount,
        sec_user_id: str,
        aweme_ids: list[str],
    ) -> None:
        if self._normalize_main_platform(account.platform_code) != "douyin":
            return

        rows = self._load_douyin_account_content_rows(db, sec_user_id=sec_user_id, aweme_ids=aweme_ids)
        now = datetime.now()
        platform_code = self._normalize_main_platform(account.platform_code)
        existing_rows = (
            db.query(PlatformAccountContent)
            .filter(
                PlatformAccountContent.owner_user_id == int(owner_id),
                PlatformAccountContent.account_id == int(account.id),
                PlatformAccountContent.platform_code == platform_code,
            )
            .all()
        )
        existing_map = {
            str(item.content_id or "").strip(): item
            for item in existing_rows
            if str(item.content_id or "").strip()
        }
        seen_content_ids: set[str] = set()

        for row in rows:
            aweme_type = str(row.get("aweme_type") or "").strip()
            content_type, content_status = self._map_douyin_content_flags(aweme_type)
            content_id = str(row.get("aweme_id") or "").strip()
            if not content_id:
                continue
            seen_content_ids.add(content_id)
            content = existing_map.get(content_id)
            if not content:
                content = PlatformAccountContent(
                    owner_user_id=int(owner_id),
                    account_id=int(account.id),
                    platform_code=platform_code,
                    content_id=content_id,
                )
                db.add(content)

            content.sec_user_id = sec_user_id or str(row.get("sec_uid") or "").strip() or None
            content.content_type = content_type
            content.content_status = content_status
            content.dy_aweme_id = content_id
            content.title = self._safe_str(row.get("title") or row.get("desc")) or content_id
            content.cover_url = self._safe_str(row.get("cover_url")) or None
            content.content_url = self._safe_str(row.get("aweme_url")) or None
            content.author_name = self._safe_str(row.get("nickname") or account.nickname or account.account_name) or None
            content.aweme_type = aweme_type or None
            content.view_count = self._safe_int(row.get("video_play_count") or row.get("view_count") or row.get("play_count"))
            content.liked_count = self._safe_int(row.get("liked_count"))
            content.comment_count = self._safe_int(row.get("comment_count"))
            content.share_count = self._safe_int(row.get("share_count"))
            content.published_at = self._parse_content_datetime(row.get("create_time"))
            content.last_synced_at = now
            content.extra_data = {
                "desc": self._safe_str(row.get("desc")) or None,
                "user_id": self._safe_str(row.get("user_id")) or None,
                "account_name": self._safe_str(account.nickname or account.account_name) or None,
            }

        for content_id, content in existing_map.items():
            if content_id in seen_content_ids:
                continue
            content.content_status = "deleted"
            content.last_synced_at = now

    def _load_douyin_account_content_rows(
        self,
        db: Session,
        *,
        sec_user_id: str,
        aweme_ids: list[str],
    ) -> list[dict[str, Any]]:
        normalized_aweme_ids = [str(item).strip() for item in aweme_ids if str(item).strip()]
        if normalized_aweme_ids:
            result = db.execute(
                text(
                    """
                    SELECT aweme_id, aweme_type, title, `desc`, aweme_url, cover_url,
                           create_time, video_play_count, liked_count, comment_count, share_count,
                           sec_uid, user_id, nickname
                    FROM douyin_aweme
                    WHERE aweme_id IN :aweme_ids
                    ORDER BY CAST(NULLIF(create_time, '') AS UNSIGNED) DESC, id DESC
                    """
                ).bindparams(bindparam("aweme_ids", expanding=True)),
                {"aweme_ids": normalized_aweme_ids},
            )
            rows = [dict(row._mapping) for row in result]
            if rows:
                return rows

        if sec_user_id:
            result = db.execute(
                text(
                    """
                    SELECT aweme_id, aweme_type, title, `desc`, aweme_url, cover_url,
                           create_time, video_play_count, liked_count, comment_count, share_count,
                           sec_uid, user_id, nickname
                    FROM douyin_aweme
                    WHERE sec_uid = :sec_user_id
                    ORDER BY CAST(NULLIF(create_time, '') AS UNSIGNED) DESC, id DESC
                    """
                ),
                {"sec_user_id": sec_user_id},
            )
            rows = [dict(row._mapping) for row in result]
            if rows:
                return rows

        if not aweme_ids:
            return []
        result = db.execute(
            text(
                """
                SELECT aweme_id, aweme_type, title, `desc`, aweme_url, cover_url,
                       create_time, video_play_count, liked_count, comment_count, share_count,
                       sec_uid, user_id, nickname
                FROM douyin_aweme
                WHERE aweme_id IN :aweme_ids
                """
            ).bindparams(bindparam("aweme_ids", expanding=True)),
            {"aweme_ids": aweme_ids},
        )
        return [dict(row._mapping) for row in result]

    @staticmethod
    def _map_douyin_content_flags(aweme_type: str) -> tuple[str, str]:
        normalized = str(aweme_type or "").strip()
        if normalized == "68":
            return "image", "published"
        if normalized == "4":
            return "video", "published"
        return "video", "published"

    @staticmethod
    def _parse_content_datetime(value: Any) -> datetime | None:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            numeric = int(float(text))
            if numeric > 0:
                return datetime.fromtimestamp(numeric)
        except (TypeError, ValueError, OSError, OverflowError):
            pass
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return None

    @staticmethod
    def _safe_int(value: Any) -> int:
        try:
            return int(float(value or 0))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _ensure_user_content_relation(
        db: Session,
        *,
        user_id: int,
        platform: str,
        relation_field: str,
        content_id: str,
        task_id: str,
    ) -> bool:
        existing = (
            db.query(UserContentRelation)
            .filter(
                UserContentRelation.user_id == user_id,
                UserContentRelation.platform == platform,
                getattr(UserContentRelation, relation_field) == content_id,
            )
            .first()
        )
        if existing:
            return False

        relation = UserContentRelation(
            user_id=user_id,
            platform=platform,
            task_id=task_id,
        )
        setattr(relation, relation_field, content_id)
        db.add(relation)
        db.flush()
        return True


platform_account_service = PlatformAccountService()
