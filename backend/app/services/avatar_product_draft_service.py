from __future__ import annotations

from typing import Any

from app.core.exceptions import ContractError
from app.db.repositories.avatar_draft_repository import AvatarDraftRecord, AvatarDraftRepository
from app.db.repositories.avatar_product_draft_repository import AvatarProductDraftRecord, AvatarProductDraftRepository
from app.db.repositories.creation_draft_repository import CreationDraftRecord, CreationDraftRepository
from app.schemas.avatar_product_draft import (
    AvatarProductDraftCreateRequest,
    AvatarProductInstructionGenerateResponse,
    AvatarProductDraftRead,
    AvatarProductDraftUpdateRequest,
)
from app.schemas.creation_draft import DigitalHumanAssetUpdateRequest
from app.services.ai_model_service import AIModelService
from app.utils.ids import generate_id


class AvatarProductDraftService:
    def __init__(
        self,
        *,
        repository: AvatarProductDraftRepository,
        avatar_repository: AvatarDraftRepository,
        creation_repository: CreationDraftRepository | None = None,
    ) -> None:
        self.repository = repository
        self.avatar_repository = avatar_repository
        self.creation_repository = creation_repository

    def initialize(self) -> None:
        self.repository.ensure_table()
        self._backfill_from_creation_drafts()

    def create(self, *, user_id: int, payload: AvatarProductDraftCreateRequest) -> AvatarProductDraftRead:
        record = AvatarProductDraftRecord(
            draft_id=generate_id("draft"),
            user_id=user_id,
            title=payload.title,
            source_url=payload.source_url,
            platform=payload.platform,
            content_id=payload.content_id,
            content_info=payload.content_info,
            transcript=payload.transcript,
            extracted_copy=payload.extracted_copy,
            rewrite_instruction=payload.rewrite_instruction,
            rewritten_copy=payload.rewritten_copy,
            voice_params=payload.voice_params,
            digital_human_params=payload.digital_human_params,
            clip_params=payload.clip_params,
            product_keyword=payload.product_keyword,
            selected_product_id=payload.selected_product_id,
            selected_product_profile=payload.selected_product_profile,
            product_assets=payload.product_assets,
            selected_white_image_id=payload.selected_white_image_id,
            selected_wear_image_id=payload.selected_wear_image_id,
            scene_image_url=payload.scene_image_url,
            image_count=payload.image_count,
            aspect_ratio=payload.aspect_ratio,
            extra_requirements=payload.extra_requirements,
            fusion_task_id=payload.fusion_task_id,
            fusion_task_status=payload.fusion_task_status,
            fusion_images=payload.fusion_images,
            selected_fusion_image_url=payload.selected_fusion_image_url,
            status=payload.status,
        )
        saved = self.repository.create(record)
        self._sync_avatar_draft(saved)
        return self._to_read(saved)

    def get(self, *, user_id: int, draft_id: str) -> AvatarProductDraftRead:
        record = self.repository.get(draft_id, user_id)
        if record is None:
            raise ContractError("产品介绍数字人草稿不存在", status_code=404)
        return self._to_read(record)

    def list_by_user(self, *, user_id: int, limit: int = 20, offset: int = 0) -> list[AvatarProductDraftRead]:
        return [self._to_read(item) for item in self.repository.list_by_user(user_id, limit=limit, offset=offset)]

    def update(self, *, user_id: int, draft_id: str, payload: AvatarProductDraftUpdateRequest) -> AvatarProductDraftRead:
        existing = self.repository.get(draft_id, user_id)
        if existing is None:
            raise ContractError("产品介绍数字人草稿不存在", status_code=404)

        record = AvatarProductDraftRecord(
            draft_id=existing.draft_id,
            user_id=existing.user_id,
            title=payload.title if payload.title is not None else existing.title,
            source_url=payload.source_url if payload.source_url is not None else existing.source_url,
            platform=payload.platform if payload.platform is not None else existing.platform,
            content_id=payload.content_id if payload.content_id is not None else existing.content_id,
            content_info=payload.content_info if payload.content_info is not None else existing.content_info,
            transcript=payload.transcript if payload.transcript is not None else existing.transcript,
            extracted_copy=payload.extracted_copy if payload.extracted_copy is not None else existing.extracted_copy,
            rewrite_instruction=payload.rewrite_instruction if payload.rewrite_instruction is not None else existing.rewrite_instruction,
            rewritten_copy=payload.rewritten_copy if payload.rewritten_copy is not None else existing.rewritten_copy,
            voice_params=payload.voice_params if payload.voice_params is not None else existing.voice_params,
            digital_human_params=payload.digital_human_params if payload.digital_human_params is not None else existing.digital_human_params,
            clip_params=payload.clip_params if payload.clip_params is not None else existing.clip_params,
            product_keyword=payload.product_keyword if payload.product_keyword is not None else existing.product_keyword,
            selected_product_id=payload.selected_product_id if payload.selected_product_id is not None else existing.selected_product_id,
            selected_product_profile=payload.selected_product_profile if payload.selected_product_profile is not None else existing.selected_product_profile,
            product_assets=payload.product_assets if payload.product_assets is not None else existing.product_assets,
            selected_white_image_id=payload.selected_white_image_id if payload.selected_white_image_id is not None else existing.selected_white_image_id,
            selected_wear_image_id=payload.selected_wear_image_id if payload.selected_wear_image_id is not None else existing.selected_wear_image_id,
            scene_image_url=payload.scene_image_url if payload.scene_image_url is not None else existing.scene_image_url,
            image_count=payload.image_count if payload.image_count is not None else existing.image_count,
            aspect_ratio=payload.aspect_ratio if payload.aspect_ratio is not None else existing.aspect_ratio,
            extra_requirements=payload.extra_requirements if payload.extra_requirements is not None else existing.extra_requirements,
            fusion_task_id=payload.fusion_task_id if payload.fusion_task_id is not None else existing.fusion_task_id,
            fusion_task_status=payload.fusion_task_status if payload.fusion_task_status is not None else existing.fusion_task_status,
            fusion_images=payload.fusion_images if payload.fusion_images is not None else existing.fusion_images,
            selected_fusion_image_url=payload.selected_fusion_image_url if payload.selected_fusion_image_url is not None else existing.selected_fusion_image_url,
            status=payload.status if payload.status is not None else existing.status,
            created_at=existing.created_at,
            updated_at=existing.updated_at,
        )
        saved = self.repository.update(record)
        self._sync_avatar_draft(saved)
        return self._to_read(saved)

    def update_digital_human_asset(
        self,
        *,
        user_id: int,
        draft_id: str,
        payload: DigitalHumanAssetUpdateRequest,
    ) -> AvatarProductDraftRead:
        existing = self.repository.get(draft_id, user_id)
        if existing is None:
            raise ContractError("产品介绍数字人草稿不存在", status_code=404)

        digital = dict(existing.digital_human_params or {})
        media_type = payload.media_type.strip().lower()
        url = payload.file_url.strip()
        if media_type == "image":
            digital["image_url"] = url
            digital["human_type"] = payload.human_type or "image"
        else:
            digital["video_url"] = url
            digital["human_type"] = payload.human_type or "video"

        record = AvatarProductDraftRecord(
            draft_id=existing.draft_id,
            user_id=existing.user_id,
            title=existing.title,
            source_url=existing.source_url,
            platform=existing.platform,
            content_id=existing.content_id,
            content_info=existing.content_info,
            transcript=existing.transcript,
            extracted_copy=existing.extracted_copy,
            rewrite_instruction=existing.rewrite_instruction,
            rewritten_copy=existing.rewritten_copy,
            voice_params=existing.voice_params,
            digital_human_params=digital,
            clip_params=existing.clip_params,
            product_keyword=existing.product_keyword,
            selected_product_id=existing.selected_product_id,
            selected_product_profile=existing.selected_product_profile,
            product_assets=existing.product_assets,
            selected_white_image_id=existing.selected_white_image_id,
            selected_wear_image_id=existing.selected_wear_image_id,
            scene_image_url=existing.scene_image_url,
            image_count=existing.image_count,
            aspect_ratio=existing.aspect_ratio,
            extra_requirements=existing.extra_requirements,
            fusion_task_id=existing.fusion_task_id,
            fusion_task_status=existing.fusion_task_status,
            fusion_images=existing.fusion_images,
            selected_fusion_image_url=existing.selected_fusion_image_url,
            status=existing.status,
            created_at=existing.created_at,
            updated_at=existing.updated_at,
        )
        saved = self.repository.update(record)
        self._sync_avatar_draft(saved)
        return self._to_read(saved)

    def generate_auto_instruction(
        self,
        *,
        user_id: int,
        draft_id: str,
        image_urls: list[str],
        product_name: str | None,
        ai_model_service: AIModelService,
    ) -> AvatarProductInstructionGenerateResponse:
        existing = self.repository.get(draft_id, user_id)
        if existing is None:
            raise ContractError("产品介绍数字人草稿不存在", status_code=404)

        cleaned_image_urls: list[str] = []
        for raw_url in image_urls:
            url = str(raw_url or "").strip()
            if url and url not in cleaned_image_urls:
                cleaned_image_urls.append(url)
        if not cleaned_image_urls:
            raise ContractError("请先提供至少一张融合图", status_code=400)

        resolved_product_name = (
            str(product_name or "").strip()
            or str((existing.selected_product_profile or {}).get("productName") or "").strip()
            or str(existing.product_keyword or "").strip()
            or "当前商品"
        )
        used_image_urls = cleaned_image_urls[:4]
        prompt = self._build_product_instruction_prompt(
            product_name=resolved_product_name,
            profile=existing.selected_product_profile or {},
            image_urls=used_image_urls,
        )
        llm_result = ai_model_service.complete_with_active_config_multimodal(
            system_prompt=(
                "You are a senior Chinese short-video director and product script planner. "
                "Analyze the provided reference images and return only the final Chinese script in the exact format requested."
            ),
            user_text=prompt,
            image_urls=used_image_urls,
            temperature=0.2,
            max_tokens=1800,
        )
        instruction = self._normalize_generated_instruction(llm_result.content)
        if not instruction:
            raise ContractError("AI 未返回可用的产品介绍脚本", status_code=502)

        record = AvatarProductDraftRecord(
            draft_id=existing.draft_id,
            user_id=existing.user_id,
            title=existing.title,
            source_url=existing.source_url,
            platform=existing.platform,
            content_id=existing.content_id,
            content_info=existing.content_info,
            transcript=existing.transcript,
            extracted_copy=existing.extracted_copy,
            rewrite_instruction=existing.rewrite_instruction,
            rewritten_copy=existing.rewritten_copy,
            voice_params=existing.voice_params,
            digital_human_params=existing.digital_human_params,
            clip_params=existing.clip_params,
            product_keyword=existing.product_keyword,
            selected_product_id=existing.selected_product_id,
            selected_product_profile=existing.selected_product_profile,
            product_assets=existing.product_assets,
            selected_white_image_id=existing.selected_white_image_id,
            selected_wear_image_id=existing.selected_wear_image_id,
            scene_image_url=existing.scene_image_url,
            image_count=existing.image_count,
            aspect_ratio=existing.aspect_ratio,
            extra_requirements=instruction,
            fusion_task_id=existing.fusion_task_id,
            fusion_task_status=existing.fusion_task_status,
            fusion_images=existing.fusion_images,
            selected_fusion_image_url=existing.selected_fusion_image_url,
            status=existing.status,
            created_at=existing.created_at,
            updated_at=existing.updated_at,
        )
        saved = self.repository.update(record)
        self._sync_avatar_draft(saved)
        return AvatarProductInstructionGenerateResponse(
            draft=self._to_read(saved),
            generated_instruction=instruction,
            used_image_urls=used_image_urls,
            llm_config_name=llm_result.config_name,
            model_name=llm_result.model_name,
        )

    def delete(self, *, user_id: int, draft_id: str) -> None:
        deleted = self.repository.delete(draft_id, user_id)
        if not deleted:
            raise ContractError("产品介绍数字人草稿不存在", status_code=404)
        self.avatar_repository.soft_delete(draft_id, user_id)

    def _sync_avatar_draft(self, record: AvatarProductDraftRecord) -> None:
        self.avatar_repository.upsert(
            AvatarDraftRecord(
                draft_id=record.draft_id,
                user_id=record.user_id,
                scene_code="product",
                title=record.title,
                status=record.status or "draft",
                current_step_code=self._resolve_current_step_code(record.status),
                progress=self._resolve_progress(record.status),
                is_deleted=0,
            )
        )

    def _backfill_from_creation_drafts(self) -> None:
        if self.creation_repository is None:
            return
        for creation_record in self.creation_repository.list_all():
            if not self._is_sales_creation_draft(creation_record):
                continue
            existing = self.repository.get(creation_record.draft_id, creation_record.user_id)
            if existing is not None:
                self._sync_avatar_draft(existing)
                continue
            saved = self.repository.create(self._from_creation_draft(creation_record))
            self._sync_avatar_draft(saved)

    @staticmethod
    def _is_sales_creation_draft(record: CreationDraftRecord) -> bool:
        digital = record.digital_human_params or {}
        content_info = record.content_info or {}
        purpose = str(digital.get("video_purpose") or content_info.get("purpose_scene") or "").strip()
        return purpose == "产品介绍数字人"

    @staticmethod
    def _from_creation_draft(record: CreationDraftRecord) -> AvatarProductDraftRecord:
        digital = record.digital_human_params or {}
        content_info = record.content_info or {}
        product_scene = digital.get("product_scene") if isinstance(digital.get("product_scene"), dict) else {}
        return AvatarProductDraftRecord(
            draft_id=record.draft_id,
            user_id=record.user_id,
            title=record.title,
            source_url=record.source_url,
            platform=record.platform,
            content_id=record.content_id,
            content_info=record.content_info,
            transcript=record.transcript,
            extracted_copy=record.extracted_copy,
            rewrite_instruction=record.rewrite_instruction,
            rewritten_copy=record.rewritten_copy,
            voice_params=record.voice_params,
            digital_human_params=record.digital_human_params,
            clip_params=record.clip_params,
            product_keyword=str(product_scene.get("product_keyword") or content_info.get("product_keyword") or "") or None,
            selected_product_id=str(product_scene.get("selected_product_id") or content_info.get("selected_product_id") or record.content_id or "") or None,
            selected_product_profile=product_scene.get("selected_product_profile") or {},
            product_assets=product_scene.get("product_assets") or [],
            selected_white_image_id=str(product_scene.get("selected_white_image_id") or "") or None,
            selected_wear_image_id=str(product_scene.get("selected_wear_image_id") or "") or None,
            scene_image_url=str(product_scene.get("scene_image_url") or "") or None,
            image_count=max(1, int(product_scene.get("image_count") or 4)),
            aspect_ratio=str(product_scene.get("aspect_ratio") or "9:16"),
            extra_requirements=str(product_scene.get("extra_requirements") or "") or None,
            fusion_task_id=str(product_scene.get("fusion_task_id") or "") or None,
            fusion_task_status=str(product_scene.get("fusion_task_status") or "") or None,
            fusion_images=product_scene.get("fusion_images") or [],
            selected_fusion_image_url=str(
                product_scene.get("selected_fusion_image_url") or digital.get("fusion_image_url") or ""
            ) or None,
            status=record.status or "draft",
        )

    @staticmethod
    def _resolve_current_step_code(status: str | None) -> str:
        status_value = (status or "").strip().lower()
        if status_value == "draft":
            return "avatar"
        if status_value == "gallery_generated":
            return "preview"
        if "fusion" in status_value:
            return "model_prompt"
        if "video" in status_value:
            return "digital_human"
        if status_value == "completed":
            return "completed"
        return "avatar"

    @staticmethod
    def _resolve_progress(status: str | None) -> int:
        status_value = (status or "").strip().lower()
        if status_value == "draft":
            return 10
        if status_value == "gallery_generated":
            return 45
        if "fusion" in status_value:
            return 70
        if "video" in status_value:
            return 85
        if status_value == "completed":
            return 100
        return 10

    @staticmethod
    def _build_product_instruction_prompt(
        *,
        product_name: str,
        profile: dict[str, Any],
        image_urls: list[str],
    ) -> str:
        lines = [
            "请基于提供的商品融合图，输出一版可直接用于产品介绍数字人的中文工作流脚本。",
            "你会收到 1 到 4 张参考图，它们来自同一组商品直播间融合图，请综合判断人物状态、产品展示方式、直播间布置和镜头感觉。",
            "只输出最终脚本文本，不要解释、不要加代码块、不要补充说明。",
            "必须严格保持下面的字段顺序、时间段顺序和“画面/口播”两行结构。",
            "总时长固定 15 秒，画面比例固定 16:9，整体必须是美妆直播间商品讲解短视频。",
            "风格固定为：高清写实、直播间种草、柔和暖光、干净高级、产品细节清晰、人物自然亲和，不要短剧感，不要古风，不要剧情对白。",
            "口播要短句、顺口、像真人直播间自然讲解，每个时间段只写一句口播。",
            "如果参考图里某些细节不够清楚，可以做合理补全，但不能偏离商品本身。",
            f"商品名称：{product_name}",
        ]
        brand_name = str(profile.get("brandName") or "").strip()
        positioning = str(profile.get("positioning") or "").strip()
        target_audience = str(profile.get("targetAudience") or "").strip()
        scenarios = str(profile.get("scenarios") or "").strip()
        tone = str(profile.get("tone") or "").strip()
        if brand_name:
            lines.append(f"品牌：{brand_name}")
        if positioning:
            lines.append(f"品牌定位：{positioning}")
        if target_audience:
            lines.append(f"目标人群：{target_audience}")
        if scenarios:
            lines.append(f"适用场景：{scenarios}")
        if tone:
            lines.append(f"品牌语气：{tone}")
        if image_urls:
            lines.append(f"参考图数量：{len(image_urls)}")
        lines.extend(
            [
                "",
                "请严格按这个格式输出：",
                "视频类型：美妆直播间商品讲解短视频",
                "视频时长：15秒",
                "画面比例：16:9",
                "参考图：四宫格美妆直播间商品展示图",
                f"商品：{product_name}",
                "风格：高清写实、直播间种草、柔和暖光、干净高级、产品细节清晰、人物自然亲和，不要短剧感，不要古风，不要剧情对白。",
                "",
                "0:00-0:03",
                "画面：",
                "口播：",
                "",
                "0:03-0:06",
                "画面：",
                "口播：",
                "",
                "0:06-0:10",
                "画面：",
                "口播：",
                "",
                "0:10-0:13",
                "画面：",
                "口播：",
                "",
                "0:13-0:15",
                "画面：",
                "口播：",
            ]
        )
        return "\n".join(lines)

    @staticmethod
    def _normalize_generated_instruction(raw: str) -> str:
        content = str(raw or "").strip()
        if content.startswith("```"):
            lines = content.splitlines()
            if lines:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        return content

    @staticmethod
    def _to_read(record: AvatarProductDraftRecord) -> AvatarProductDraftRead:
        return AvatarProductDraftRead(
            draft_id=record.draft_id,
            user_id=record.user_id,
            title=record.title,
            source_url=record.source_url,
            platform=record.platform,
            content_id=record.content_id,
            content_info=record.content_info,
            transcript=record.transcript,
            extracted_copy=record.extracted_copy,
            rewrite_instruction=record.rewrite_instruction,
            rewritten_copy=record.rewritten_copy,
            voice_params=record.voice_params,
            digital_human_params=record.digital_human_params,
            clip_params=record.clip_params,
            product_keyword=record.product_keyword,
            selected_product_id=record.selected_product_id,
            selected_product_profile=record.selected_product_profile,
            product_assets=record.product_assets,
            selected_white_image_id=record.selected_white_image_id,
            selected_wear_image_id=record.selected_wear_image_id,
            scene_image_url=record.scene_image_url,
            image_count=record.image_count,
            aspect_ratio=record.aspect_ratio,
            extra_requirements=record.extra_requirements,
            fusion_task_id=record.fusion_task_id,
            fusion_task_status=record.fusion_task_status,
            fusion_images=record.fusion_images,
            selected_fusion_image_url=record.selected_fusion_image_url,
            status=record.status,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

