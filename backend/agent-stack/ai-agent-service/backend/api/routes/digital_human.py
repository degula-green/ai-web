# -*- coding: utf-8 -*-
"""Digital human API.

Image-based digital human uses scene-specific RunningHub AI Apps.
Video-based retalk remains on DashScope videoretalk.
Model scene additionally supports gallery generation and multimodal prompt analysis.
"""

from typing import Any, Dict, Literal, Optional
import tempfile
from pathlib import Path

import httpx

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage

from services.dashscope_s2v import DashScopeS2VError, create_videoretalk_task, get_task
from llm_provider import get_multimodal_llm
from services.llm_config_service import llm_config_service
from services.runninghub_workflow import (
    RunningHubWorkflowError,
    query_workflow_task,
    submit_ai_app,
    upload_binary_from_url,
)
from services.image_utils import build_multimodal_content
from utils.logger import logger

router = APIRouter()

DEFAULT_S2V_CONFIG_NAME = "wan2.2-s2v"
DEFAULT_VIDEOTALK_CONFIG_NAME = "videoretalk"

PURPOSE_TALK = "口播数字人"
PURPOSE_SALES = "卖货数字人"
PURPOSE_SALES_ALIAS = "带货数字人"
PURPOSE_PRODUCT = "产品介绍数字人"
PURPOSE_MODEL = "模特数字人"
PURPOSE_CLIP = "视频剪辑数字人"

SCENE_SPEECH = "speech_avatar"
SCENE_MODEL = "model_avatar"

RUNNINGHUB_SCENE_CONFIGS: dict[str, dict[str, Any]] = {
    PURPOSE_TALK: {
        "scene_key": SCENE_SPEECH,
        "app_id": "2051914471551062018",
        "resolution_node_id": "17",
        "image_node_id": "15",
        "audio_node_id": "16",
        "text_node_id": "43",
        "start_time_node_id": "83",
        "start_time": "0:00",
        "end_time_node_id": "83",
        "end_time": "1:00",
        "default_resolution": "1080x1920 (9:16) (竖屏)",
        "resolution_map": {
            "480P": "1080x1920 (9:16) (竖屏)",
            "720P": "1920x1080 (16:9) (横屏)",
            "1080P": "1920x1080 (16:9) (横屏)",
            "16:9": "1920x1080 (16:9) (横屏)",
            "9:16": "1080x1920 (9:16) (竖屏)",
            "1:1": "1024x1024 (1:1) (方形)",
        },
        "requires_audio": True,
    },
    PURPOSE_SALES: {
        "scene_key": SCENE_SPEECH,
        "app_id": "2051631559354138626",
        "resolution_node_id": "183",
        "image_node_id": "174",
        "audio_node_id": "177",
        "text_node_id": "208",
        "default_resolution": "1280x720 (16:9) (横屏)",
        "resolution_map": {
            "480P": "854x480 (16:9) (横屏)",
            "720P": "1280x720 (16:9) (横屏)",
            "1080P": "1920x1080 (16:9) (横屏)",
            "16:9": "1280x720 (16:9) (横屏)",
            "9:16": "1080x1920 (9:16) (竖屏)",
            "1:1": "1024x1024 (1:1) (方形)",
        },
        "requires_audio": True,
    },
    PURPOSE_CLIP: {
        "scene_key": SCENE_SPEECH,
        "app_id": "2051914471551062018",
        "resolution_node_id": "17",
        "image_node_id": "15",
        "audio_node_id": "16",
        "text_node_id": "43",
        "start_time_node_id": "83",
        "start_time": "0:00",
        "end_time_node_id": "83",
        "end_time": "1:00",
        "default_resolution": "1920x1080 (16:9) (横屏)",
        "resolution_map": {
            "480P": "854x480 (16:9) (横屏)",
            "720P": "1920x1080 (16:9) (横屏)",
            "1080P": "1920x1080 (16:9) (横屏)",
            "16:9": "1920x1080 (16:9) (横屏)",
            "9:16": "1080x1920 (9:16) (竖屏)",
            "1:1": "1024x1024 (1:1) (方形)",
        },
        "requires_audio": True,
    },
    PURPOSE_PRODUCT: {
        "scene_key": SCENE_MODEL,
        "app_id": "2051652722474135553",
        "resolution_node_id": "54",
        "image_node_id": "88",
        "text_node_id": "9",
        "default_resolution": "1080x1920 (9:16) (竖屏)",
        "resolution_map": {
            "480P": "1080x1920 (9:16) (竖屏)",
            "720P": "1920x1080 (16:9) (横屏)",
            "1080P": "1920x1080 (16:9) (横屏)",
            "16:9": "1920x1080 (16:9) (横屏)",
            "9:16": "1080x1920 (9:16) (竖屏)",
            "1:1": "1024x1024 (1:1) (方形)",
        },
        "requires_audio": False,
    },
    PURPOSE_MODEL: {
        "scene_key": SCENE_MODEL,
        "app_id": "2051652722474135553",
        "resolution_node_id": "54",
        "image_node_id": "88",
        "text_node_id": "9",
        "default_resolution": "1080x1920 (9:16) (绔栧睆)",
        "resolution_map": {
            "480P": "1080x1920 (9:16) (绔栧睆)",
            "720P": "1080x1920 (9:16) (绔栧睆)",
        },
        "requires_audio": False,
    },
}
MODEL_GALLERY_APP_ID = "2041754379371421697"


class DetectRequest(BaseModel):
    image_url: str = Field(..., description="Public image URL")
    purpose_scene: str | None = Field(default=None, description="Business scene label")


class DetectResponse(BaseModel):
    raw: Dict[str, Any] = Field(..., description="Detection result")


class S2VJobRequest(BaseModel):
    image_url: str = Field(..., description="Public image URL")
    audio_url: str | None = Field(default=None, description="Public audio URL")
    script_text: str = Field(..., description="Prompt or rewritten script text")
    resolution: str = Field(default="480P", description="Logical resolution or RunningHub resolution value")
    aspect_ratio: str | None = Field(default=None, description="Aspect ratio hint from frontend")
    style: Literal["speech", "singing", "performance"] = "speech"
    purpose_scene: str | None = Field(default=None, description="Business scene label")


class S2VJobResponse(BaseModel):
    task_id: Optional[str] = None
    task_status: Optional[str] = None
    request_id: Optional[str] = None
    raw: Dict[str, Any] = Field(default_factory=dict)


class SubmitPipelineRequest(BaseModel):
    image_url: str
    audio_url: str | None = None
    script_text: str
    resolution: str = "480P"
    aspect_ratio: str | None = None
    style: Literal["speech", "singing", "performance"] = "speech"
    skip_detect: bool = Field(False, description="Reserved for compatibility")
    purpose_scene: str | None = Field(default=None, description="Business scene label")


class SubmitPipelineResponse(BaseModel):
    detect: Optional[Dict[str, Any]] = None
    job: Dict[str, Any]


class VideoRetalkJobRequest(BaseModel):
    video_url: str = Field(..., description="Public video URL")
    audio_url: str = Field(..., description="Public audio URL")
    ref_image_url: Optional[str] = Field(None, description="Optional face reference image URL")
    video_extension: bool = Field(False, description="Extend video duration if audio is longer")
    query_face_threshold: Optional[int] = Field(
        None,
        ge=120,
        le=200,
        description="Optional face match threshold",
    )


class VideoRetalkSubmitResponse(BaseModel):
    job: Dict[str, Any]


class ModelGalleryGenerateRequest(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=128)
    product_white_image_url: str = Field(..., min_length=1)
    product_wear_image_url: str = Field(..., min_length=1)
    model_image_url: str = Field(..., min_length=1)
    scene_image_url: str | None = None
    image_count: int = Field(default=8, ge=4, le=12)
    aspect_ratio: str = Field(default="3:4")
    extra_requirements: str | None = None


class ModelImageAnalysisRequest(BaseModel):
    selected_image_urls: list[str] = Field(..., min_length=4, max_length=4)
    product_name: str = Field(..., min_length=1, max_length=128)
    brand_name: str | None = None
    positioning: str | None = None
    target_audience: str | None = None
    tone: str | None = None
    extra_requirements: str | None = None


class ModelImageAnalysisResponse(BaseModel):
    prompt_text: str


class ModelRequirementSuggestRequest(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=128)
    brand_name: str | None = None
    product_white_image_url: str = Field(..., min_length=1)
    product_wear_image_url: str = Field(..., min_length=1)
    model_image_url: str = Field(..., min_length=1)
    scene_image_url: str | None = None
    image_count: int = Field(default=8, ge=4, le=12)


class ModelRequirementSuggestResponse(BaseModel):
    requirement_text: str


def _normalize_model_gallery_aspect_ratio(value: str | None) -> str:
    normalized = (value or "").strip().replace("：", ":").replace("?", ":")
    allowed_map = {
        "1:1": "1：1",
        "3:4": "3：4",
        "9:16": "9：16",
    }
    return allowed_map.get(normalized, "3：4")


async def _load_s2v_credentials(config_name: str) -> Dict[str, Any]:
    row = await llm_config_service.get_config(config_name, include_api_key=True)
    if not row:
        raise HTTPException(status_code=400, detail=f"Missing llm_configs entry: {config_name}")
    key = row.get("api_key")
    if not key:
        raise HTTPException(status_code=400, detail=f"Config {config_name} is missing api_key")
    base = row.get("base_url") or "https://www.runninghub.cn"
    model_name = row.get("model_name") or ""
    return {"api_key": key, "base_url": base, "model_name": model_name}


def _resolve_scene_config(purpose_scene: str | None) -> dict[str, Any]:
    key = str(purpose_scene or PURPOSE_TALK).strip()
    if key == PURPOSE_SALES_ALIAS:
        key = PURPOSE_SALES
    return RUNNINGHUB_SCENE_CONFIGS.get(key, RUNNINGHUB_SCENE_CONFIGS[PURPOSE_TALK])


def _resolve_runninghub_resolution(scene_config: dict[str, Any], resolution: str) -> str:
    raw = str(resolution or "").strip()
    if not raw:
        return str(scene_config["default_resolution"])
    if "(" in raw and "x" in raw:
        return raw
    mapped = scene_config.get("resolution_map", {}).get(raw.upper())
    if mapped:
        return str(mapped)
    mapped = scene_config.get("resolution_map", {}).get(raw)
    return str(mapped or scene_config["default_resolution"])


def _build_model_gallery_prompt(
    *,
    product_name: str,
    image_count: int,
    extra_requirements: str | None,
) -> str:
    lines = [
        f"【产品】：{product_name}",
        f"【数量】：{image_count}",
        "【强制要求】：",
        "保持同一位模特、同一张脸、同一发型、同一身材比例。",
        "产品主体要清晰，服装或配饰细节真实，避免变形、融化、多余人物和错误手部。",
    ]
    if extra_requirements and extra_requirements.strip():
        lines.append(extra_requirements.strip())
    return "\n".join(lines)


def _build_runninghub_node_info_list(
    *,
    scene_config: dict[str, Any],
    image_file_name: str,
    audio_file_name: str | None,
    script_text: str,
    resolution: str,
) -> list[dict[str, str]]:
    node_info_list: list[dict[str, str]] = [
        {
            "nodeId": str(scene_config["resolution_node_id"]),
            "fieldName": "resolution",
            "fieldValue": _resolve_runninghub_resolution(scene_config, resolution),
        },
        {
            "nodeId": str(scene_config["image_node_id"]),
            "fieldName": "image",
            "fieldValue": image_file_name,
        },
        {
            "nodeId": str(scene_config["text_node_id"]),
            "fieldName": "text",
            "fieldValue": script_text,
        },
    ]
    start_time_node_id = scene_config.get("start_time_node_id")
    if start_time_node_id and scene_config.get("start_time"):
        node_info_list.append(
            {
                "nodeId": str(start_time_node_id),
                "fieldName": "start_time",
                "fieldValue": str(scene_config["start_time"]),
            }
        )
    end_time_node_id = scene_config.get("end_time_node_id")
    if end_time_node_id and scene_config.get("end_time"):
        node_info_list.append(
            {
                "nodeId": str(end_time_node_id),
                "fieldName": "end_time",
                "fieldValue": str(scene_config["end_time"]),
            }
        )
    audio_node_id = scene_config.get("audio_node_id")
    if audio_node_id and audio_file_name:
        node_info_list.append(
            {
                "nodeId": str(audio_node_id),
                "fieldName": "audio",
                "fieldValue": audio_file_name,
            }
        )
    return node_info_list


def _build_runninghub_detect_result(image_url: str, purpose_scene: str | None) -> Dict[str, Any]:
    scene_config = _resolve_scene_config(purpose_scene)
    return {
        "provider": "runninghub",
        "scene_key": scene_config["scene_key"],
        "output": {
            "check_pass": True,
            "skipped": True,
            "image_url": image_url,
        },
    }


def _wrap_runninghub_submit(job: Dict[str, Any], scene_config: dict[str, Any]) -> Dict[str, Any]:
    return {
        "scene_key": scene_config["scene_key"],
        "output": {
            "task_id": job.get("taskId"),
            "task_status": job.get("status"),
        },
        "request_id": job.get("clientId"),
        "raw": job,
    }


def _wrap_runninghub_task(data: Dict[str, Any]) -> Dict[str, Any]:
    results = data.get("results") or []
    if isinstance(results, dict):
        results = [results]

    normalized_results = []
    primary_video_url = ""
    for item in results:
        url = item.get("url") or ""
        output_type = str(item.get("outputType") or "").lower()
        normalized_item = {
            "url": url,
            "video_url": url,
            "text": item.get("text"),
            "node_id": item.get("nodeId"),
            "output_type": output_type,
        }
        normalized_results.append(normalized_item)
        if not primary_video_url and output_type in {"mp4", "mov", "webm", "mkv"}:
            primary_video_url = url

    if not primary_video_url and normalized_results:
        primary_video_url = normalized_results[0].get("url") or ""

    return {
        "output": {
            "task_id": data.get("taskId"),
            "task_status": data.get("status"),
            "results": normalized_results,
            "video_url": primary_video_url,
        },
        "request_id": data.get("clientId"),
        "raw": data,
    }


async def _download_image_to_temp(url: str, temp_dir: Path, index: int) -> Path:
    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").lower()
        if "png" in content_type:
            path = temp_dir / f"image_{index}.png"
            path.write_bytes(response.content)
            return path
        if "jpeg" in content_type or "jpg" in content_type:
            path = temp_dir / f"image_{index}.jpg"
            path.write_bytes(response.content)
            return path

        # Some multimodal providers reject webp/gif/bmp payloads even when the
        # image bytes are valid, so normalize those assets to JPEG first.
        try:
            from PIL import Image
            import io

            image = Image.open(io.BytesIO(response.content))
            if image.mode in ("RGBA", "LA", "P"):
                converted = Image.new("RGB", image.size, (255, 255, 255))
                converted.paste(image.convert("RGBA"), mask=image.convert("RGBA").split()[-1])
                image = converted
            elif image.mode != "RGB":
                image = image.convert("RGB")

            path = temp_dir / f"image_{index}.jpg"
            image.save(path, format="JPEG", quality=92)
            return path
        except Exception:
            path = temp_dir / f"image_{index}.jpg"
            path.write_bytes(response.content)
            return path


async def _submit_runninghub_image_job(
    *,
    cred: Dict[str, Any],
    image_url: str,
    audio_url: str | None,
    script_text: str,
    resolution: str,
    purpose_scene: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    scene_config = _resolve_scene_config(purpose_scene)
    app_id = str(scene_config.get("app_id") or "").strip()
    if not app_id:
        raise HTTPException(status_code=400, detail=f"RunningHub app_id not configured for scene: {purpose_scene or PURPOSE_TALK}")
    image_upload = await upload_binary_from_url(cred["api_key"], image_url, base_url=cred["base_url"])

    audio_file_name: str | None = None
    if scene_config.get("requires_audio"):
        if not audio_url or not str(audio_url).strip():
            raise HTTPException(status_code=400, detail="This digital human scene requires audio_url")
        audio_upload = await upload_binary_from_url(cred["api_key"], audio_url, base_url=cred["base_url"])
        audio_file_name = str(audio_upload["fileName"])

    job = await submit_ai_app(
        cred["api_key"],
        app_id,
        _build_runninghub_node_info_list(
            scene_config=scene_config,
            image_file_name=str(image_upload["fileName"]),
            audio_file_name=audio_file_name,
            script_text=script_text.strip(),
            resolution=resolution,
        ),
        base_url=cred["base_url"],
    )
    return job, scene_config


async def _submit_model_gallery_job(
    *,
    cred: Dict[str, Any],
    product_white_image_url: str,
    product_wear_image_url: str,
    model_image_url: str,
    scene_image_url: str | None,
    product_name: str,
    image_count: int,
    aspect_ratio: str,
    extra_requirements: str | None,
) -> Dict[str, Any]:
    white_upload = await upload_binary_from_url(cred["api_key"], product_white_image_url, base_url=cred["base_url"])
    wear_upload = await upload_binary_from_url(cred["api_key"], product_wear_image_url, base_url=cred["base_url"])
    model_upload = await upload_binary_from_url(cred["api_key"], model_image_url, base_url=cred["base_url"])
    scene_source = (scene_image_url or "").strip() or product_wear_image_url
    scene_upload = await upload_binary_from_url(cred["api_key"], scene_source, base_url=cred["base_url"])

    node_info_list = [
        {"nodeId": "10", "fieldName": "image", "fieldValue": str(white_upload["fileName"])},
        {"nodeId": "51", "fieldName": "image", "fieldValue": str(wear_upload["fileName"])},
        {"nodeId": "49", "fieldName": "image", "fieldValue": str(model_upload["fileName"])},
        {"nodeId": "44", "fieldName": "image", "fieldValue": str(scene_upload["fileName"])},
        {
            "nodeId": "5",
            "fieldName": "text",
            "fieldValue": _build_model_gallery_prompt(
                product_name=product_name,
                image_count=image_count,
                extra_requirements=extra_requirements,
            ),
        },
        {"nodeId": "79", "fieldName": "text", "fieldValue": _normalize_model_gallery_aspect_ratio(aspect_ratio)},
    ]

    return await submit_ai_app(
        cred["api_key"],
        MODEL_GALLERY_APP_ID,
        node_info_list,
        base_url=cred["base_url"],
    )


async def _analyze_model_images_with_multimodal_llm(request: ModelImageAnalysisRequest) -> str:
    system_prompt = (
        "你是电商模特视频提示词生成助手。"
        "用户会提供 4 张已经选定的模特展示图，以及产品和品牌上下文。"
        "请基于图片内容和产品信息，输出一段中文提示词，用于生成一个四宫格关键帧硬切的电商模特展示视频。"
        "要求保留同一模特、同一张脸、同一身材比例，强调真实电商棚拍质感、服装细节和构图连续性。"
        "只输出最终提示词正文，不要解释。"
    )
    user_text_parts = [
        f"产品名称：{request.product_name}",
    ]
    if request.brand_name:
        user_text_parts.append(f"品牌名称：{request.brand_name}")
    if request.positioning:
        user_text_parts.append(f"产品定位：{request.positioning}")
    if request.target_audience:
        user_text_parts.append(f"目标人群：{request.target_audience}")
    if request.tone:
        user_text_parts.append(f"调性：{request.tone}")
    if request.extra_requirements:
        user_text_parts.append(f"额外要求：{request.extra_requirements.strip()}")
    user_text_parts.append("请结合这 4 张图的构图、服装细节、动作和场景，生成最终视频提示词。")
    user_text = "\n".join(user_text_parts)

    temp_dir_ctx = tempfile.TemporaryDirectory(prefix="model_scene_mm_")
    try:
        temp_dir = Path(temp_dir_ctx.name)
        image_paths: list[str] = []
        for index, url in enumerate(request.selected_image_urls, start=1):
            path = await _download_image_to_temp(url, temp_dir, index)
            image_paths.append(str(path))

        llm = get_multimodal_llm(temperature=0.3)
        content = build_multimodal_content(user_text, image_paths, max_images=4)
        response = await llm.ainvoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=content),
            ]
        )
        content_out = response.content
        if isinstance(content_out, str):
            return content_out.strip()
        return str(content_out).strip()
    finally:
        temp_dir_ctx.cleanup()


async def _suggest_model_requirements_with_multimodal_llm(request: ModelRequirementSuggestRequest) -> str:
    system_prompt = (
        "你是电商模特图组需求生成助手。"
        "用户会提供产品白底图、产品佩戴图、指定模特图、可选场景图，以及要生成的张数。"
        "请根据这些参考图，输出一段中文的图组生成补充要求。"
        "要求内容可直接用于图片生成工作流，突出人物一致性、产品清晰度、场景变化和镜头变化。"
        "请按以下格式输出：先写【强制要求】：再逐条写第1张、第2张直到最后一张。"
        "只输出正文，不要解释。"
    )
    user_text_parts = [
        f"产品名称：{request.product_name}",
        f"生成张数：{request.image_count}",
    ]
    if request.brand_name:
        user_text_parts.append(f"品牌名称：{request.brand_name}")
    user_text_parts.append(
        "请综合分析产品白底图中的产品主体、佩戴图中的展示方式、模特图的人物条件、场景图的空间氛围，"
        "给出适合连续图组生成的补充要求。"
    )
    user_text = "\n".join(user_text_parts)

    image_urls = [
        request.product_white_image_url,
        request.product_wear_image_url,
        request.model_image_url,
    ]
    if request.scene_image_url and request.scene_image_url.strip():
        image_urls.append(request.scene_image_url.strip())

    temp_dir_ctx = tempfile.TemporaryDirectory(prefix="model_scene_requirements_")
    try:
        temp_dir = Path(temp_dir_ctx.name)
        image_paths: list[str] = []
        for index, url in enumerate(image_urls, start=1):
            path = await _download_image_to_temp(url, temp_dir, index)
            image_paths.append(str(path))

        llm = get_multimodal_llm(temperature=0.3)
        content = build_multimodal_content(user_text, image_paths, max_images=4)
        response = await llm.ainvoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=content),
            ]
        )
        content_out = response.content
        if isinstance(content_out, str):
            return content_out.strip()
        return str(content_out).strip()
    finally:
        temp_dir_ctx.cleanup()


@router.post("/s2v/detect", response_model=DetectResponse)
async def s2v_detect(
    body: DetectRequest,
    config_name: str = Query(default=DEFAULT_S2V_CONFIG_NAME, description="llm_configs.config_name"),
):
    await _load_s2v_credentials(config_name)
    return DetectResponse(raw=_build_runninghub_detect_result(body.image_url, body.purpose_scene))


@router.post("/s2v/jobs", response_model=S2VJobResponse)
async def s2v_create_job(
    body: S2VJobRequest,
    config_name: str = Query(default=DEFAULT_S2V_CONFIG_NAME),
):
    cred = await _load_s2v_credentials(config_name)
    try:
        data, scene_config = await _submit_runninghub_image_job(
            cred=cred,
            image_url=body.image_url,
            audio_url=body.audio_url,
            script_text=body.script_text,
            resolution=body.resolution,
            purpose_scene=body.purpose_scene,
        )
    except RunningHubWorkflowError as e:
        logger.warning("runninghub image submit failed: {}", e)
        raise HTTPException(status_code=e.status_code or 502, detail=str(e)) from e

    wrapped = _wrap_runninghub_submit(data, scene_config)
    out = wrapped.get("output") or {}
    return S2VJobResponse(
        task_id=out.get("task_id"),
        task_status=out.get("task_status"),
        request_id=wrapped.get("request_id"),
        raw=wrapped,
    )


@router.get("/s2v/tasks/{task_id}")
async def s2v_get_task(
    task_id: str,
    config_name: str = Query(default=DEFAULT_S2V_CONFIG_NAME),
):
    cred = await _load_s2v_credentials(config_name)
    try:
        data = await query_workflow_task(cred["api_key"], task_id, base_url=cred["base_url"])
    except RunningHubWorkflowError as e:
        logger.warning("runninghub task query failed: {}", e)
        raise HTTPException(status_code=e.status_code or 502, detail=str(e)) from e
    return _wrap_runninghub_task(data)


@router.post("/s2v/submit", response_model=SubmitPipelineResponse)
async def s2v_submit_pipeline(
    body: SubmitPipelineRequest,
    config_name: str = Query(default=DEFAULT_S2V_CONFIG_NAME),
):
    cred = await _load_s2v_credentials(config_name)
    detect_raw = None if body.skip_detect else _build_runninghub_detect_result(body.image_url, body.purpose_scene)

    try:
        job, scene_config = await _submit_runninghub_image_job(
            cred=cred,
            image_url=body.image_url,
            audio_url=body.audio_url,
            script_text=body.script_text,
            resolution=body.resolution,
            purpose_scene=body.purpose_scene,
        )
    except RunningHubWorkflowError as e:
        raise HTTPException(status_code=e.status_code or 502, detail=str(e)) from e

    return SubmitPipelineResponse(detect=detect_raw, job=_wrap_runninghub_submit(job, scene_config))


@router.post("/runninghub/tasks/{task_id}")
async def runninghub_get_task(
    task_id: str,
    config_name: str = Query(default=DEFAULT_S2V_CONFIG_NAME),
):
    cred = await _load_s2v_credentials(config_name)
    try:
        data = await query_workflow_task(cred["api_key"], task_id, base_url=cred["base_url"])
    except RunningHubWorkflowError as e:
        logger.warning("runninghub task query failed: {}", e)
        raise HTTPException(status_code=e.status_code or 502, detail=str(e)) from e
    return _wrap_runninghub_task(data)


@router.post("/model-image-gallery/submit", response_model=SubmitPipelineResponse)
async def model_image_gallery_submit(
    body: ModelGalleryGenerateRequest,
    config_name: str = Query(default=DEFAULT_S2V_CONFIG_NAME),
):
    cred = await _load_s2v_credentials(config_name)
    try:
        job = await _submit_model_gallery_job(
            cred=cred,
            product_white_image_url=body.product_white_image_url,
            product_wear_image_url=body.product_wear_image_url,
            model_image_url=body.model_image_url,
            scene_image_url=body.scene_image_url,
            product_name=body.product_name,
            image_count=body.image_count,
            aspect_ratio=body.aspect_ratio,
            extra_requirements=body.extra_requirements,
        )
    except RunningHubWorkflowError as e:
        logger.warning("runninghub model gallery submit failed: {}", e)
        raise HTTPException(status_code=e.status_code or 502, detail=str(e)) from e
    return SubmitPipelineResponse(
        detect={
            "provider": "runninghub",
            "scene_key": "model_gallery",
        },
        job=_wrap_runninghub_submit(job, {"scene_key": "model_gallery"}),
    )


@router.post("/model-image-gallery/analyze", response_model=ModelImageAnalysisResponse)
async def model_image_gallery_analyze(body: ModelImageAnalysisRequest):
    try:
        prompt_text = await _analyze_model_images_with_multimodal_llm(body)
    except Exception as e:
        logger.warning("model image analysis failed: {}", e)
        raise HTTPException(status_code=500, detail=f"妯＄壒鍥惧垎鏋愬け璐? {e}") from e
    return ModelImageAnalysisResponse(prompt_text=prompt_text)


@router.post("/model-image-gallery/suggest-requirements", response_model=ModelRequirementSuggestResponse)
async def model_image_gallery_suggest_requirements(body: ModelRequirementSuggestRequest):
    try:
        requirement_text = await _suggest_model_requirements_with_multimodal_llm(body)
    except Exception as e:
        logger.warning("model requirement suggestion failed: {}", e)
        raise HTTPException(status_code=500, detail=f"妯＄壒鍥剧粍瑕佹眰鐢熸垚澶辫触: {e}") from e
    return ModelRequirementSuggestResponse(requirement_text=requirement_text)


@router.post("/videoretalk/jobs", response_model=S2VJobResponse)
async def videoretalk_create_job(
    body: VideoRetalkJobRequest,
    config_name: str = Query(default=DEFAULT_VIDEOTALK_CONFIG_NAME),
):
    cred = await _load_s2v_credentials(config_name)
    try:
        data = await create_videoretalk_task(
            cred["api_key"],
            body.video_url,
            body.audio_url,
            model=cred.get("model_name") or "videoretalk",
            ref_image_url=body.ref_image_url,
            video_extension=body.video_extension,
            query_face_threshold=body.query_face_threshold,
            base_url=cred["base_url"],
        )
    except DashScopeS2VError as e:
        logger.warning("videoretalk submit failed: {}", e)
        raise HTTPException(status_code=e.status_code or 502, detail=str(e)) from e

    out = data.get("output") or {}
    return S2VJobResponse(
        task_id=out.get("task_id"),
        task_status=out.get("task_status"),
        request_id=data.get("request_id"),
        raw=data,
    )


@router.get("/videoretalk/tasks/{task_id}")
async def videoretalk_get_task(
    task_id: str,
    config_name: str = Query(default=DEFAULT_VIDEOTALK_CONFIG_NAME),
):
    cred = await _load_s2v_credentials(config_name)
    try:
        data = await get_task(cred["api_key"], task_id, base_url=cred["base_url"])
    except DashScopeS2VError as e:
        logger.warning("videoretalk get_task failed: {}", e)
        raise HTTPException(status_code=e.status_code or 502, detail=str(e)) from e
    return data


@router.post("/videoretalk/submit", response_model=VideoRetalkSubmitResponse)
async def videoretalk_submit_pipeline(
    body: VideoRetalkJobRequest,
    config_name: str = Query(default=DEFAULT_VIDEOTALK_CONFIG_NAME),
):
    cred = await _load_s2v_credentials(config_name)
    try:
        job = await create_videoretalk_task(
            cred["api_key"],
            body.video_url,
            body.audio_url,
            model=cred.get("model_name") or "videoretalk",
            ref_image_url=body.ref_image_url,
            video_extension=body.video_extension,
            query_face_threshold=body.query_face_threshold,
            base_url=cred["base_url"],
        )
    except DashScopeS2VError as e:
        raise HTTPException(status_code=e.status_code or 502, detail=str(e)) from e
    return VideoRetalkSubmitResponse(job=job)
