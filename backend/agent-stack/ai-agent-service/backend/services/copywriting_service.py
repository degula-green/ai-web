# -*- coding: utf-8 -*-
"""
轻量文案服务

提供两个能力：
1. 从 URL 提取文案：parse_link -> fetch_content -> 按需转录 -> LLM 提取文案
2. 轻量改写文案：直接调用 LLM 对文本改写
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from agent.errors import RemixToolException
from agent.tools.video_processor_tool import _process_video_internal
from llm_provider import get_llm
from schemas import ContentParseResponse
from services.download_server_client import (
    ContentNotFoundError,
    CookiesNotFoundError,
    DownloadServerClient,
    DownloadServerError,
)
from services.link_parser import LinkParser
from services.llm_config_service import llm_config_service
from utils.logger import logger
from utils.srt_from_transcript import transcript_dict_to_srt


EXTRACT_SYSTEM_PROMPT = """你是一个文案提取助手。

你的目标是从社媒内容信息中整理出适合继续编辑或数字人口播的原始文案。

要求：
1. 尽量忠实原内容，不添加创意延展，不补充新观点。
2. 可以清理明显的口头禅、重复句、乱码、无意义平台噪音。
3. 保留原有信息顺序和表达意图。
4. 只输出整理后的文案正文，不要解释，不要加标题。"""


REWRITE_SYSTEM_PROMPT = """你是一个轻量文案改写助手。

要求：
1. 在保留原意的前提下，让表达更顺畅、更自然。
2. 不要扩写过多，不要新增事实。
3. 默认输出适合口播的简洁中文。
4. 只输出改写后的正文，不要解释。"""


def _normalize_url(url: str) -> str:
    url = (url or "").strip()
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


async def _get_first_llm_config_row() -> Dict[str, Any]:
    row = await llm_config_service.get_first_config(include_api_key=False)
    if not row:
        raise ValueError("尚未配置大模型，请先在 llm_configs 中添加至少一条配置。")
    return row


async def _get_first_llm_config_name() -> str:
    row = await _get_first_llm_config_row()
    config_name = row.get("config_name")
    if not config_name:
        raise ValueError("llm_configs 第一条配置缺少 config_name。")
    return config_name


def _build_extract_input(content_info: ContentParseResponse, transcript_text: str) -> str:
    parts = [
        f"平台: {content_info.platform.value}",
        f"内容类型: {content_info.content_type.value}",
        f"标题: {content_info.title or ''}",
        f"描述: {content_info.desc or ''}",
    ]

    if transcript_text:
        parts.append(f"视频转录:\n{transcript_text}")

    parts.append(
        "请基于以上信息，整理出可直接继续编辑或用于数字人口播的原始文案。"
        "如果标题和描述已经足够完整，就优先保留标题和描述内容；"
        "如果视频转录更完整，则以转录为主。"
    )
    return "\n\n".join(parts)


async def _invoke_llm(system_prompt: str, user_prompt: str) -> str:
    config_name = await _get_first_llm_config_name()
    llm = get_llm(
        config_name=config_name,
        enable_thinking=False,
        temperature=0.2,
    )
    response = await llm.ainvoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
    )
    content = response.content
    if isinstance(content, str):
        return content.strip()
    return str(content).strip()


def _is_downloadable_media_url(url: Optional[str]) -> bool:
    if not url:
        return False
    lowered = url.lower()
    return any(
        marker in lowered
        for marker in (
            ".mp4",
            ".m3u8",
            ".flv",
            ".webm",
            ".m4s",
            ".wav",
            ".mp3",
            ".m4a",
            "bilivideo",
            "mcdn.bilivideo",
            "douyinvod",
            "bytedance",
            "kuaishou",
            "kwaicdn",
            "xhscdn",
            "/resource/",
            "/video/",
        )
    )


async def _transcribe_if_needed(content_info: ContentParseResponse) -> Optional[Dict[str, Any]]:
    if content_info.content_type.value == "image":
        return None

    asr_url = content_info.audio_url or content_info.video_url
    if not _is_downloadable_media_url(asr_url):
        logger.info("Skip transcription because media url is not directly downloadable")
        return None

    result = await _process_video_internal(
        asr_url,
        step_callback=None,
        persist_video=False,
    )
    return {
        "text": result.text,
        "segments": result.segments,
        "content_id": content_info.content_id,
    }


class CopywritingService:
    """轻量文案服务"""

    def __init__(self):
        self.link_parser = LinkParser()
        self.download_client = DownloadServerClient()

    async def extract_from_url(
        self,
        url: str,
        user_id: Optional[str] = None,
        *,
        include_transcript_srt: bool = False,
    ) -> Dict[str, Any]:
        normalized_url = _normalize_url(url)
        if not normalized_url:
            raise ValueError("URL 不能为空。")

        parsed = self.link_parser.parse(normalized_url)
        if not parsed:
            raise ValueError("无法识别该链接，请确认是小红书、抖音、B站或快手内容链接。")

        try:
            content_info = await self.download_client.fetch_content(normalized_url, user_id=user_id)
        except ContentNotFoundError as e:
            raise ValueError(f"内容不存在或已失效: {e}") from e
        except CookiesNotFoundError as e:
            raise ValueError(f"缺少平台 Cookies: {e}") from e
        except DownloadServerError as e:
            raise ValueError(f"抓取内容失败: {e}") from e

        transcript = None
        try:
            transcript = await _transcribe_if_needed(content_info)
        except RemixToolException as e:
            logger.warning("Transcription failed but extraction continues: {}", e)
        except Exception as e:
            logger.warning("Unexpected transcription failure but extraction continues: {}", e)

        extracted_copy = await _invoke_llm(
            EXTRACT_SYSTEM_PROMPT,
            _build_extract_input(content_info, (transcript or {}).get("text", "")),
        )

        config_row = await _get_first_llm_config_row()
        transcript_srt = None
        if include_transcript_srt and transcript:
            transcript_srt = transcript_dict_to_srt(transcript)

        return {
            "url": normalized_url,
            "parsed_link": {
                "platform": parsed.platform.value,
                "content_id": parsed.content_id,
                "original_url": parsed.original_url,
                "is_short_link": parsed.is_short_link,
            },
            "content_info": content_info.model_dump(),
            "transcript": transcript,
            "transcript_srt": transcript_srt,
            "extracted_copy": extracted_copy,
            "llm_config_name": config_row.get("config_name"),
            "model_name": config_row.get("model_name"),
        }

    async def rewrite_text(self, text: str, instruction: Optional[str] = None) -> Dict[str, Any]:
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            raise ValueError("待改写文案不能为空。")

        user_prompt = cleaned_text
        if instruction and instruction.strip():
            user_prompt = f"改写要求：{instruction.strip()}\n\n原文：\n{cleaned_text}"

        rewritten_text = await _invoke_llm(REWRITE_SYSTEM_PROMPT, user_prompt)
        config_row = await _get_first_llm_config_row()
        return {
            "source_text": cleaned_text,
            "rewritten_text": rewritten_text,
            "instruction": (instruction or "").strip() or None,
            "llm_config_name": config_row.get("config_name"),
            "model_name": config_row.get("model_name"),
        }


copywriting_service = CopywritingService()
