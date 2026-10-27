# -*- coding: utf-8 -*-
# Copyright (c) 2026 relakkes@gmail.com
#
# This file is part of MediaCrawlerPro-ContentRemixAgent project.
# Repository: https://github.com/MediaCrawlerPro/MediaCrawlerPro-ContentRemixAgent/blob/main/backend/services/cookies_service.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#
# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。

"""
平台 Cookies 读取服务（对接主项目平台账号体系）

数据来源:
- platform_accounts
- platform_account_sessions
"""
import json
from typing import List, Optional

import aiomysql

from config import settings
from schemas import CookiesInfo, CookiesDetail


class CookiesNotConfiguredError(Exception):
    """Cookies 未配置或已失效"""
    pass


class CookiesService:
    """平台 Cookies 服务（主项目适配）"""

    def __init__(self):
        self._pool: Optional[aiomysql.Pool] = None

    async def _get_pool(self) -> aiomysql.Pool:
        """获取 Agent 数据库连接池"""
        if self._pool is None:
            self._pool = await aiomysql.create_pool(
                host=settings.AGENT_DB_HOST or "localhost",
                port=settings.AGENT_DB_PORT or 3306,
                user=settings.AGENT_DB_USER or "root",
                password=settings.AGENT_DB_PASSWORD or "",
                db=settings.AGENT_DB_NAME,
                charset="utf8mb4",
                autocommit=True,
                minsize=1,
                maxsize=5,
            )
        return self._pool

    async def close(self):
        """关闭数据库连接池"""
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None

    @staticmethod
    def _normalize_platform(platform: str) -> str:
        key = (platform or "").strip().lower()
        return {
            "dy": "douyin",
            "douyin": "douyin",
            "xhs": "xiaohongshu",
            "xiaohongshu": "xiaohongshu",
            "bili": "bilibili",
            "bilibili": "bilibili",
            "ks": "kuaishou",
            "kuaishou": "kuaishou",
        }.get(key, key)

    @staticmethod
    def _cookie_items_to_string(items: list) -> str:
        pairs: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            value = str(item.get("value") or "").strip()
            if name:
                pairs.append(f"{name}={value}")
        return "; ".join(pairs)

    async def get_cookies(self, platform: str, user_id: Optional[str] = None) -> str:
        """
        获取指定平台的有效 cookies

        Args:
            platform: 平台标识 (xhs/dy/bili/ks)
            user_id: 可选，主项目用户 ID（iam_users.id）

        Returns:
            cookies 字符串

        Raises:
            CookiesNotConfiguredError: 未找到有效的 cookies
        """
        detail = await self.get_detail(platform=platform, user_id=user_id)
        if not detail or not detail.cookies:
            raise CookiesNotConfiguredError(
                f"未找到平台 {platform} 的有效 cookies，请先在主程序完成账号授权"
            )
        return detail.cookies

    async def get_detail(self, platform: str, user_id: Optional[str] = None) -> Optional[CookiesDetail]:
        """
        获取指定平台的 cookies 详情（含 cookies 明文）

        Args:
            platform: 平台标识 (xhs/dy/bili/ks)
            user_id: 可选，主项目用户 ID（iam_users.id）

        Returns:
            CookiesDetail 或 None
        """
        pool = await self._get_pool()
        normalized_platform = self._normalize_platform(platform)
        resolved_user_id = int(user_id) if user_id is not None and str(user_id).isdigit() else None

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                sql = """
                    SELECT
                        pa.platform_code AS platform_code,
                        ps.cookies AS cookies_json,
                        ps.cookie_blob AS cookie_blob,
                        ps.status AS session_status,
                        pa.auth_status AS account_status,
                        pa.updated_at AS updated_at
                    FROM platform_accounts pa
                    JOIN platform_account_sessions ps ON ps.account_id = pa.id
                    WHERE pa.platform_code = %s
                      AND pa.is_deleted = 0
                """
                params: list = [normalized_platform]
                if resolved_user_id is not None:
                    sql += " AND pa.owner_user_id = %s"
                    params.append(resolved_user_id)
                sql += """
                    ORDER BY
                        CASE WHEN ps.status = 'active' THEN 0 ELSE 1 END,
                        CASE WHEN pa.auth_status IN ('authorized','active','valid') THEN 0 ELSE 1 END,
                        ps.updated_at DESC,
                        pa.updated_at DESC
                    LIMIT 1
                """
                await cursor.execute(sql, tuple(params))
                row = await cursor.fetchone()
                if not row:
                    return None

                cookies_str = ""
                cookies_json = row.get("cookies_json")
                if isinstance(cookies_json, list):
                    cookies_str = self._cookie_items_to_string(cookies_json)
                elif isinstance(cookies_json, str):
                    try:
                        parsed = json.loads(cookies_json)
                        if isinstance(parsed, list):
                            cookies_str = self._cookie_items_to_string(parsed)
                    except Exception:
                        cookies_str = ""
                if not cookies_str:
                    blob = row.get("cookie_blob")
                    if isinstance(blob, str):
                        try:
                            parsed_blob = json.loads(blob)
                            if isinstance(parsed_blob, list):
                                cookies_str = self._cookie_items_to_string(parsed_blob)
                            else:
                                cookies_str = blob
                        except Exception:
                            cookies_str = blob

                status = 0 if row.get("session_status") == "active" else 1
                return CookiesDetail(
                    platform=platform,
                    cookies=cookies_str,
                    status=status,
                    remark=f"source=platform_accounts({normalized_platform})",
                    updated_at=row["updated_at"].isoformat() if row.get("updated_at") else "",
                )

    async def set_cookies(self, platform: str, cookies: str, remark: Optional[str] = None) -> None:
        raise NotImplementedError("请在主程序账号授权流程中维护 Cookies，不支持在 ContentRemixAgent 直接写入。")

    async def list_all(self, user_id: Optional[str] = None) -> List[CookiesInfo]:
        """
        列出所有平台 cookies（不返回 cookies 明文）

        Returns:
            CookiesInfo 列表
        """
        pool = await self._get_pool()
        resolved_user_id = int(user_id) if user_id is not None and str(user_id).isdigit() else None

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                sql = """
                    SELECT
                        pa.platform_code,
                        pa.auth_status,
                        ps.status AS session_status,
                        GREATEST(IFNULL(pa.updated_at, '1970-01-01'), IFNULL(ps.updated_at, '1970-01-01')) AS updated_at
                    FROM platform_accounts pa
                    LEFT JOIN platform_account_sessions ps ON ps.account_id = pa.id
                    WHERE pa.is_deleted = 0
                """
                params: list = []
                if resolved_user_id is not None:
                    sql += " AND pa.owner_user_id = %s"
                    params.append(resolved_user_id)
                sql += " ORDER BY updated_at DESC"

                await cursor.execute(sql, tuple(params))
                rows = await cursor.fetchall()

                # platform 去重（每个平台取最新一条）
                seen: set[str] = set()
                result: list[CookiesInfo] = []
                reverse_map = {
                    "douyin": "dy",
                    "xiaohongshu": "xhs",
                    "bilibili": "bili",
                    "kuaishou": "ks",
                }
                for row in rows:
                    platform_code = row.get("platform_code")
                    if platform_code in seen:
                        continue
                    seen.add(platform_code)
                    display_platform = reverse_map.get(platform_code, platform_code)
                    status = 0 if row.get("session_status") == "active" else 1
                    result.append(
                        CookiesInfo(
                            platform=display_platform,
                            status=status,
                            remark=f"account_status={row.get('auth_status')}",
                            updated_at=row["updated_at"].isoformat() if row.get("updated_at") else "",
                        )
                    )
                return result

    async def delete_cookies(self, platform: str) -> bool:
        """
        删除指定平台 cookies

        Args:
            platform: 平台标识

        Returns:
            是否删除成功（True 表示找到并删除了记录）
        """
        raise NotImplementedError("请在主程序账号授权流程中维护 Cookies，不支持在 ContentRemixAgent 直接删除。")

    async def update_status(self, platform: str, status: int) -> bool:
        """
        更新 cookies 状态

        Args:
            platform: 平台标识
            status: 状态 (0=有效, 1=过期, 2=禁用)

        Returns:
            是否更新成功
        """
        raise NotImplementedError("请在主程序账号授权流程中维护 Cookies，不支持在 ContentRemixAgent 直接改状态。")


# 创建全局服务实例
cookies_service = CookiesService()
