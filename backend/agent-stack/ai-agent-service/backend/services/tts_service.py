# -*- coding: utf-8 -*-
"""
TTS service.

Responsibilities:
- Manage local voice_asset / voice_generation_record tables
- Call DashScope CosyVoice voice enrollment APIs
- Call DashScope CosyVoice speech synthesis APIs
- Persist preview/generated audio files to local assets for debugging/preview
"""

from __future__ import annotations

import base64
import json
import secrets
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import aiomysql
import httpx

from config import settings
from services.llm_config_service import llm_config_service
from utils.logger import logger


class TTSServiceError(Exception):
    """Raised when local TTS workflow fails."""


class DashScopeTTSAPIError(TTSServiceError):
    """Raised when DashScope TTS APIs return an error."""

    def __init__(self, message: str, status_code: int = 502, payload: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload or {}


class TTSService:
    DEFAULT_TTS_CONFIG_NAME = "cosyvoice-v3.5-plus"
    DEFAULT_ENROLLMENT_CONFIG_NAME = "voice-enrollment"

    def __init__(self) -> None:
        self._pool: Optional[aiomysql.Pool] = None
        self.assets_dir = Path(settings.ASSETS_DIR)
        self.url_prefix = settings.ASSETS_URL_PREFIX.rstrip("/")

    async def _get_pool(self) -> aiomysql.Pool:
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

    async def close(self) -> None:
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None

    async def _load_llm_config(self, config_name: str) -> Dict[str, Any]:
        row = await llm_config_service.get_config(config_name, include_api_key=True)
        if not row:
            raise TTSServiceError(f"未找到 llm_configs 配置: {config_name}")
        if not row.get("api_key"):
            raise TTSServiceError(f"配置 {config_name} 未设置 api_key")
        return {
            "config_name": config_name,
            "api_key": row["api_key"],
            "base_url": (row.get("base_url") or "https://dashscope.aliyuncs.com").rstrip("/"),
            "model_name": row.get("model_name") or config_name,
            "provider": row.get("provider") or "openai",
        }

    async def _post_json(
        self,
        *,
        api_key: str,
        base_url: str,
        path: str,
        payload: dict,
    ) -> dict:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        url = f"{base_url.rstrip('/')}{path}"
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, headers=headers, json=payload)

        try:
            data = response.json()
        except Exception:
            data = {"raw_text": response.text}

        if response.status_code >= 400:
            message = (
                data.get("message")
                or data.get("code")
                or data.get("raw_text")
                or f"DashScope API 请求失败: HTTP {response.status_code}"
            )
            raise DashScopeTTSAPIError(
                message=str(message),
                status_code=response.status_code,
                payload=data if isinstance(data, dict) else {},
            )

        return data if isinstance(data, dict) else {"data": data}

    async def _delete_json(
        self,
        *,
        api_key: str,
        base_url: str,
        path: str,
        payload: dict,
    ) -> dict:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        url = f"{base_url.rstrip('/')}{path}"
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.request("POST", url, headers=headers, json=payload)

        try:
            data = response.json()
        except Exception:
            data = {"raw_text": response.text}

        if response.status_code >= 400:
            message = (
                data.get("message")
                or data.get("code")
                or data.get("raw_text")
                or f"DashScope API 请求失败: HTTP {response.status_code}"
            )
            raise DashScopeTTSAPIError(
                message=str(message),
                status_code=response.status_code,
                payload=data if isinstance(data, dict) else {},
            )

        return data if isinstance(data, dict) else {"data": data}

    async def download_file(self, file_url: str) -> bytes:
        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
            response = await client.get(file_url)
            response.raise_for_status()
            return response.content

    def _safe_ext(self, name: str, default: str = ".bin") -> str:
        ext = Path(name).suffix.lower()
        return ext if ext and len(ext) <= 8 else default

    def _make_relative_asset_url(self, *parts: str) -> str:
        clean_parts = [p.strip("/\\") for p in parts if p]
        return f"{self.url_prefix}/{'/'.join(clean_parts)}"

    def _resolve_asset_path(self, *parts: str) -> Path:
        clean_parts = [p.strip("/\\") for p in parts if p]
        path = self.assets_dir.joinpath(*clean_parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def persist_binary_asset(self, *, content: bytes, category: str, filename: str) -> str:
        now = datetime.now()
        relative_parts = (
            "tts",
            category,
            now.strftime("%Y%m%d"),
            filename,
        )
        target = self._resolve_asset_path(*relative_parts)
        target.write_bytes(content)
        return self._make_relative_asset_url(*relative_parts)

    def persist_base64_asset(self, *, b64_data: str, category: str, filename: str) -> str:
        return self.persist_binary_asset(
            content=base64.b64decode(b64_data),
            category=category,
            filename=filename,
        )

    def build_absolute_url(self, base_url: str, url_or_path: Optional[str]) -> Optional[str]:
        if not url_or_path:
            return url_or_path
        if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
            return url_or_path
        return f"{base_url.rstrip('/')}{url_or_path}"

    def _resolve_owner_user_id(self, user_id: Optional[str]) -> Optional[int]:
        if user_id is None:
            return None
        user_id_str = str(user_id).strip()
        if not user_id_str or not user_id_str.isdigit():
            return None
        return int(user_id_str)

    async def list_voice_assets(
        self,
        *,
        keyword: Optional[str] = None,
        source_type: Optional[str] = None,
        status: Optional[str] = "enabled",
        page: int = 1,
        page_size: int = 50,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        pool = await self._get_pool()
        offset = max(page - 1, 0) * page_size
        conditions = ["deleted_at IS NULL"]
        params: list[Any] = []
        resolved_user_id = self._resolve_owner_user_id(user_id)

        if resolved_user_id is not None:
            conditions.append("(source_type = 'system_builtin' OR is_public = 1 OR owner_user_id = %s)")
            params.append(resolved_user_id)
        else:
            conditions.append("(source_type = 'system_builtin' OR is_public = 1)")

        if status:
            conditions.append("status = %s")
            params.append(status)
        if source_type:
            conditions.append("source_type = %s")
            params.append(source_type)
        if keyword:
            conditions.append("(voice_name LIKE %s OR voice_code LIKE %s OR third_party_voice_id LIKE %s)")
            like = f"%{keyword}%"
            params.extend([like, like, like])

        where = " AND ".join(conditions)

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(f"SELECT COUNT(*) AS cnt FROM voice_asset WHERE {where}", tuple(params))
                total_row = await cursor.fetchone()

                await cursor.execute(
                    f"""
                    SELECT *
                    FROM voice_asset
                    WHERE {where}
                    ORDER BY is_public DESC, sort_no ASC, id DESC
                    LIMIT %s OFFSET %s
                    """,
                    tuple(params + [page_size, offset]),
                )
                rows = await cursor.fetchall()

        return {"list": rows, "total": int(total_row["cnt"] if total_row else 0)}

    async def get_voice_asset_by_id(self, voice_asset_id: int) -> Optional[Dict[str, Any]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "SELECT * FROM voice_asset WHERE id = %s AND deleted_at IS NULL LIMIT 1",
                    (voice_asset_id,),
                )
                return await cursor.fetchone()

    async def get_voice_asset_by_voice_id(self, third_party_voice_id: str) -> Optional[Dict[str, Any]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    """
                    SELECT *
                    FROM voice_asset
                    WHERE third_party_voice_id = %s AND deleted_at IS NULL
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (third_party_voice_id,),
                )
                return await cursor.fetchone()

    async def create_voice_asset(self, payload: Dict[str, Any]) -> int:
        pool = await self._get_pool()
        fields = list(payload.keys())
        values = [payload[k] for k in fields]
        placeholders = ", ".join(["%s"] * len(fields))
        columns = ", ".join([f"`{name}`" for name in fields])

        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    f"INSERT INTO voice_asset ({columns}) VALUES ({placeholders})",
                    tuple(values),
                )
                return int(cursor.lastrowid)

    async def update_voice_asset(self, voice_asset_id: int, payload: Dict[str, Any]) -> bool:
        if not payload:
            return False
        pool = await self._get_pool()
        assignments = ", ".join([f"`{name}` = %s" for name in payload.keys()])
        values = list(payload.values()) + [voice_asset_id]
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    f"UPDATE voice_asset SET {assignments} WHERE id = %s",
                    tuple(values),
                )
                return cursor.rowcount > 0

    async def soft_delete_voice_asset_by_voice_id(self, third_party_voice_id: str) -> bool:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    UPDATE voice_asset
                    SET deleted_at = NOW(), status = 'disabled'
                    WHERE third_party_voice_id = %s AND deleted_at IS NULL
                    """,
                    (third_party_voice_id,),
                )
                return cursor.rowcount > 0

    async def create_generation_record(self, payload: Dict[str, Any]) -> int:
        pool = await self._get_pool()
        fields = list(payload.keys())
        values = [payload[k] for k in fields]
        placeholders = ", ".join(["%s"] * len(fields))
        columns = ", ".join([f"`{name}`" for name in fields])
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    f"INSERT INTO voice_generation_record ({columns}) VALUES ({placeholders})",
                    tuple(values),
                )
                return int(cursor.lastrowid)

    async def update_generation_record(self, record_id: int, payload: Dict[str, Any]) -> bool:
        if not payload:
            return False
        pool = await self._get_pool()
        assignments = ", ".join([f"`{name}` = %s" for name in payload.keys()])
        values = list(payload.values()) + [record_id]
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    f"UPDATE voice_generation_record SET {assignments} WHERE id = %s",
                    tuple(values),
                )
                return cursor.rowcount > 0

    async def list_remote_voices(
        self,
        *,
        enrollment_config_name: str,
        prefix: Optional[str] = None,
        page_index: int = 0,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        config = await self._load_llm_config(enrollment_config_name)
        payload = {
            "model": "voice-enrollment",
            "input": {
                "action": "list_voice",
                "page_index": page_index,
                "page_size": page_size,
            },
        }
        if prefix:
            payload["input"]["prefix"] = prefix
        return await self._post_json(
            api_key=config["api_key"],
            base_url=config["base_url"],
            path="/api/v1/services/audio/tts/customization",
            payload=payload,
        )

    async def query_remote_voice(self, *, enrollment_config_name: str, voice_id: str) -> Dict[str, Any]:
        config = await self._load_llm_config(enrollment_config_name)
        payload = {
            "model": "voice-enrollment",
            "input": {"action": "query_voice", "voice_id": voice_id},
        }
        return await self._post_json(
            api_key=config["api_key"],
            base_url=config["base_url"],
            path="/api/v1/services/audio/tts/customization",
            payload=payload,
        )

    async def delete_remote_voice(self, *, enrollment_config_name: str, voice_id: str) -> Dict[str, Any]:
        config = await self._load_llm_config(enrollment_config_name)
        payload = {
            "model": "voice-enrollment",
            "input": {"action": "delete_voice", "voice_id": voice_id},
        }
        return await self._delete_json(
            api_key=config["api_key"],
            base_url=config["base_url"],
            path="/api/v1/services/audio/tts/customization",
            payload=payload,
        )

    async def create_voice_clone(
        self,
        *,
        enrollment_config_name: str,
        target_model: str,
        prefix: str,
        audio_url: str,
        language_hints: Optional[list[str]] = None,
        max_prompt_audio_length: Optional[float] = None,
        enable_preprocess: Optional[bool] = None,
    ) -> Dict[str, Any]:
        config = await self._load_llm_config(enrollment_config_name)
        input_payload: Dict[str, Any] = {
            "action": "create_voice",
            "target_model": target_model,
            "prefix": prefix,
            "url": audio_url,
        }
        if language_hints:
            input_payload["language_hints"] = language_hints[:1]
        if max_prompt_audio_length is not None:
            input_payload["max_prompt_audio_length"] = max_prompt_audio_length
        if enable_preprocess is not None:
            input_payload["enable_preprocess"] = enable_preprocess

        payload = {"model": "voice-enrollment", "input": input_payload}
        return await self._post_json(
            api_key=config["api_key"],
            base_url=config["base_url"],
            path="/api/v1/services/audio/tts/customization",
            payload=payload,
        )

    async def create_voice_design(
        self,
        *,
        enrollment_config_name: str,
        target_model: str,
        prefix: str,
        voice_prompt: str,
        preview_text: str,
        language_hints: Optional[list[str]] = None,
        sample_rate: int = 24000,
        response_format: str = "wav",
    ) -> Dict[str, Any]:
        config = await self._load_llm_config(enrollment_config_name)
        input_payload: Dict[str, Any] = {
            "action": "create_voice",
            "target_model": target_model,
            "voice_prompt": voice_prompt,
            "preview_text": preview_text,
            "prefix": prefix,
        }
        if language_hints:
            input_payload["language_hints"] = language_hints[:1]

        payload = {
            "model": "voice-enrollment",
            "input": input_payload,
            "parameters": {
                "sample_rate": sample_rate,
                "response_format": response_format,
            },
        }
        return await self._post_json(
            api_key=config["api_key"],
            base_url=config["base_url"],
            path="/api/v1/services/audio/tts/customization",
            payload=payload,
        )

    async def synthesize_speech(
        self,
        *,
        tts_config_name: str,
        model_name: Optional[str],
        text: str,
        voice_id: str,
        audio_format: str = "mp3",
        sample_rate: Optional[int] = None,
        volume: Optional[int] = None,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        language_hints: Optional[list[str]] = None,
        instruction: Optional[str] = None,
        seed: Optional[int] = None,
        enable_ssml: Optional[bool] = None,
        word_timestamp_enabled: Optional[bool] = None,
    ) -> Dict[str, Any]:
        config = await self._load_llm_config(tts_config_name)
        input_payload: Dict[str, Any] = {
            "text": text,
            "voice": voice_id,
            "format": audio_format,
        }
        if sample_rate is not None:
            input_payload["sample_rate"] = sample_rate
        if volume is not None:
            input_payload["volume"] = volume
        if rate is not None:
            input_payload["rate"] = rate
        if pitch is not None:
            input_payload["pitch"] = pitch
        if language_hints:
            input_payload["language_hints"] = language_hints[:1]
        if instruction:
            input_payload["instruction"] = instruction
        if seed is not None:
            input_payload["seed"] = seed
        if enable_ssml is not None:
            input_payload["enable_ssml"] = enable_ssml
        if word_timestamp_enabled is not None:
            input_payload["word_timestamp_enabled"] = word_timestamp_enabled

        payload = {
            "model": model_name or config["model_name"],
            "input": input_payload,
        }
        return await self._post_json(
            api_key=config["api_key"],
            base_url=config["base_url"],
            path="/api/v1/services/audio/tts/SpeechSynthesizer",
            payload=payload,
        )

    def _new_voice_code(self, prefix: str = "voice") -> str:
        return f"{prefix}_{secrets.token_hex(8)}"

    def _new_record_code(self) -> str:
        return f"tts_{secrets.token_hex(8)}"

    def _normalize_decimal(self, value: Optional[float]) -> Optional[Decimal]:
        if value is None:
            return None
        return Decimal(str(value))

    def _filename_from_provider_url(self, provider_url: str, fallback_stem: str, fallback_ext: str) -> str:
        path = urlparse(provider_url).path
        ext = self._safe_ext(path, fallback_ext)
        return f"{fallback_stem}{ext}"

    async def create_local_voice_asset_from_clone(
        self,
        *,
        target_model: str,
        prefix: str,
        source_audio_url: str,
        remote_response: Dict[str, Any],
        language: Optional[str],
        owner_user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        voice_id = ((remote_response.get("output") or {}).get("voice_id") or "").strip()
        if not voice_id:
            raise TTSServiceError("声音复刻成功但未返回 voice_id")

        payload = {
            "voice_code": self._new_voice_code("clone"),
            "voice_name": prefix,
            "source_type": "user_clone",
            "provider": "dashscope",
            "model_name": target_model,
            "target_model": target_model,
            "third_party_voice_id": voice_id,
            "voice_language": language,
            "sample_audio_url": source_audio_url,
            "status": "deploying",
            "is_public": 0,
            "owner_user_id": self._resolve_owner_user_id(owner_user_id),
            "remark": "created via API",
            "ext_json": json.dumps(remote_response, ensure_ascii=False),
        }
        voice_asset_id = await self.create_voice_asset(payload)
        return {
            "id": voice_asset_id,
            "voice_id": voice_id,
            "status": "deploying",
            "request_id": remote_response.get("request_id"),
        }

    async def create_local_voice_asset_from_design(
        self,
        *,
        target_model: str,
        prefix: str,
        voice_prompt: str,
        preview_text: str,
        response_format: str,
        sample_rate: int,
        language: Optional[str],
        remote_response: Dict[str, Any],
        owner_user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        output = remote_response.get("output") or {}
        voice_id = (output.get("voice_id") or "").strip()
        preview_audio = output.get("preview_audio") or {}
        preview_b64 = preview_audio.get("data") or ""
        if not voice_id:
            raise TTSServiceError("声音设计成功但未返回 voice_id")

        preview_audio_url = None
        if preview_b64:
            preview_audio_url = self.persist_base64_asset(
                b64_data=preview_b64,
                category="preview",
                filename=f"{voice_id}_preview.{response_format}",
            )

        remote_for_storage = dict(remote_response)
        output_for_storage = dict(output)
        if output_for_storage.get("preview_audio"):
            preview_audio_for_storage = dict(output_for_storage["preview_audio"])
            preview_audio_for_storage.pop("data", None)
            output_for_storage["preview_audio"] = preview_audio_for_storage
        remote_for_storage["output"] = output_for_storage

        payload = {
            "voice_code": self._new_voice_code("design"),
            "voice_name": prefix,
            "source_type": "ai_design",
            "provider": "dashscope",
            "model_name": target_model,
            "target_model": target_model,
            "third_party_voice_id": voice_id,
            "voice_language": language,
            "voice_prompt": voice_prompt,
            "preview_text": preview_text,
            "preview_audio_url": preview_audio_url,
            "status": "enabled",
            "is_public": 0,
            "owner_user_id": self._resolve_owner_user_id(owner_user_id),
            "remark": f"preview_format={response_format}, sample_rate={sample_rate}",
            "ext_json": json.dumps(remote_for_storage, ensure_ascii=False),
        }
        voice_asset_id = await self.create_voice_asset(payload)
        return {
            "id": voice_asset_id,
            "voice_id": voice_id,
            "preview_audio_url": preview_audio_url,
            "request_id": remote_response.get("request_id"),
        }

    async def sync_voice_asset_status(
        self,
        *,
        voice_id: str,
        remote_output: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        asset = await self.get_voice_asset_by_voice_id(voice_id)
        if not asset:
            return None

        remote_status = remote_output.get("status")
        payload: Dict[str, Any] = {
            "status": "enabled" if remote_status == "OK" else "failed" if remote_status == "UNDEPLOYED" else "deploying",
            "target_model": remote_output.get("target_model") or asset.get("target_model"),
            "voice_prompt": remote_output.get("voice_prompt") or asset.get("voice_prompt"),
            "preview_text": remote_output.get("preview_text") or asset.get("preview_text"),
            "sample_audio_url": remote_output.get("resource_link") or asset.get("sample_audio_url"),
            "ext_json": json.dumps(remote_output, ensure_ascii=False),
        }
        await self.update_voice_asset(int(asset["id"]), payload)
        return await self.get_voice_asset_by_id(int(asset["id"]))

    async def generate_audio(
        self,
        *,
        draft_id: Optional[int],
        voice_asset_id: Optional[int],
        user_id: Optional[str],
        direct_voice_id: Optional[str],
        text: str,
        style: Optional[str],
        speed: Optional[float],
        volume: Optional[float],
        pitch: Optional[float],
        language: Optional[str],
        audio_format: str,
        sample_rate: Optional[int],
        tts_config_name: str,
    ) -> Dict[str, Any]:
        voice_asset = None
        voice_id = (direct_voice_id or "").strip()
        model_name = None
        provider = "dashscope"

        if voice_asset_id:
            voice_asset = await self.get_voice_asset_by_id(voice_asset_id)
            if not voice_asset:
                raise TTSServiceError(f"未找到声音资产: {voice_asset_id}")
            resolved_user_id = self._resolve_owner_user_id(user_id)
            asset_owner_user_id = voice_asset.get("owner_user_id")
            if (
                (voice_asset.get("source_type") or "") != "system_builtin"
                and voice_asset.get("is_public") != 1
                and asset_owner_user_id is not None
                and resolved_user_id is not None
                and int(asset_owner_user_id) != resolved_user_id
            ):
                raise TTSServiceError("无权使用该用户音色")
            voice_id = (voice_asset.get("third_party_voice_id") or "").strip()
            model_name = voice_asset.get("target_model") or voice_asset.get("model_name")
            provider = voice_asset.get("provider") or provider

        if not voice_id:
            raise TTSServiceError("缺少可用的 voice_id")

        config = await self._load_llm_config(tts_config_name)
        if not model_name:
            model_name = config["model_name"]

        record_id = await self.create_generation_record(
            {
                "record_code": self._new_record_code(),
                "draft_id": draft_id,
                "voice_asset_id": voice_asset_id,
                "provider": provider,
                "model_name": model_name,
                "third_party_voice_id": voice_id,
                "input_text": text,
                "style": style,
                "speed": self._normalize_decimal(speed),
                "volume": self._normalize_decimal(volume),
                "pitch": self._normalize_decimal(pitch),
                "audio_format": audio_format,
                "status": "processing",
            }
        )

        try:
            instruction = style
            if voice_asset and (voice_asset.get("source_type") or "") == "system_builtin":
                # Most system voices do not support free-form instruction.
                instruction = None

            remote = await self.synthesize_speech(
                tts_config_name=tts_config_name,
                model_name=model_name,
                text=text,
                voice_id=voice_id,
                audio_format=audio_format,
                sample_rate=sample_rate,
                volume=int(round((volume or 1.0) * 50)) if volume is not None else None,
                rate=speed,
                pitch=pitch,
                language_hints=[language] if language else None,
                instruction=instruction,
            )
            output = remote.get("output") or {}
            audio = output.get("audio") or {}
            provider_audio_url = audio.get("url")
            if not provider_audio_url:
                raise TTSServiceError("语音生成成功但未返回 audio.url")

            binary = await self.download_file(provider_audio_url)
            filename = self._filename_from_provider_url(
                provider_audio_url,
                fallback_stem=remote.get("request_id") or f"record_{record_id}",
                fallback_ext=f".{audio_format}",
            )
            local_audio_url = self.persist_binary_asset(
                content=binary,
                category="generated",
                filename=filename,
            )

            await self.update_generation_record(
                record_id,
                {
                    "audio_url": provider_audio_url,
                    "request_id": remote.get("request_id"),
                    "status": "success",
                    "raw_response": json.dumps(
                        {
                            **remote,
                            "local_audio_url": local_audio_url,
                        },
                        ensure_ascii=False,
                    ),
                },
            )
            return {
                "record_id": record_id,
                "audio_url": provider_audio_url,
                "local_audio_url": local_audio_url,
                "request_id": remote.get("request_id"),
                "expires_at": audio.get("expires_at"),
                "voice_id": voice_id,
                "voice_asset_id": voice_asset_id,
            }
        except Exception as exc:
            logger.exception("TTS generate failed")
            await self.update_generation_record(
                record_id,
                {
                    "status": "failed",
                    "error_code": exc.__class__.__name__,
                    "error_message": str(exc),
                },
            )
            raise


tts_service = TTSService()
