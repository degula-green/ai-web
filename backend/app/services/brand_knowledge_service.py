from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.adapters.storage.base import BaseObjectStorage
from app.core.exceptions import ContractError
from app.db.models.brand_knowledge import BrandProduct, BrandSellingPoint, BrandVisualAsset
from app.db.repositories.brand_knowledge_repository import BrandKnowledgeRepository

SELLING_POINT_TYPES = {"required", "optional", "forbidden"}
SELLING_POINT_SOURCES = {"manual", "ai", "external"}
SELLING_POINT_STATUSES = {"draft", "pending_confirm", "confirmed", "rejected"}
ASSET_API_TO_DB = {
    "logo": "brand_logo",
    "ui": "product_ui",
    "promo": "promo_img",
    "video": "video_asset",
    "product": "product_ui",
}
ASSET_DB_TO_API = {
    "brand_logo": "logo",
    "product_ui": "ui",
    "promo_img": "promo",
    "video_asset": "video",
}


class BrandKnowledgeService:
    def __init__(self, *, repository: BrandKnowledgeRepository, storage_adapter: BaseObjectStorage) -> None:
        self.repository = repository
        self.storage_adapter = storage_adapter

    def list_products(
        self,
        *,
        owner_user_id: int,
        keyword: str | None,
        page_no: int,
        page_size: int,
        sort_by: str,
    ) -> dict[str, Any]:
        data = self.repository.list_products(
            owner_user_id=owner_user_id,
            keyword=keyword,
            page_no=page_no,
            page_size=page_size,
            sort_by=sort_by,
        )
        rows: list[BrandProduct] = data["list"]
        product_ids = [int(row.id) for row in rows]
        selling_counts = self.repository.count_product_selling_points(product_ids=product_ids)
        asset_counts = self.repository.count_product_visual_assets(product_ids=product_ids)
        return {
            "pageNo": page_no,
            "pageSize": page_size,
            "total": data["total"],
            "list": [
                {
                    "brandId": str(row.id),
                    "brandName": row.brand_name,
                    "productName": row.product_name,
                    "coverUrl": row.cover_url,
                    "sellingPointsCount": int(selling_counts.get(int(row.id), 0)),
                    "visualAssetsCount": int(asset_counts.get(int(row.id), 0)),
                    "updatedAt": self._fmt_dt(row.updated_at),
                }
                for row in rows
            ],
        }

    def create_product(self, *, owner_user_id: int, operator_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.repository.create_product(
            owner_user_id=owner_user_id,
            operator_id=operator_id,
            payload={
                "brand_name": payload["brandName"].strip(),
                "product_name": payload["productName"].strip(),
                "positioning": payload.get("positioning"),
                "target_audience": payload.get("targetAudience"),
                "scenarios": payload.get("scenarios"),
                "tone_voice": payload.get("tone"),
                "forbidden_phrases": self._normalize_string_list(payload.get("forbiddenPhrases")),
                "cover_url": payload.get("coverUrl"),
            },
        )
        return {"brandId": str(row.id)}

    def get_product_detail(self, *, owner_user_id: int, brand_id: int) -> dict[str, Any]:
        row = self.repository.get_product_for_owner(owner_user_id=owner_user_id, brand_id=brand_id)
        if not row:
            raise ContractError("品牌档案不存在", status_code=404)
        return self._map_product(row)

    def update_product(
        self,
        *,
        owner_user_id: int,
        brand_id: int,
        operator_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        row = self.repository.update_product(
            owner_user_id=owner_user_id,
            brand_id=brand_id,
            operator_id=operator_id,
            payload={
                "brand_name": payload["brandName"].strip(),
                "product_name": payload["productName"].strip(),
                "positioning": payload.get("positioning"),
                "target_audience": payload.get("targetAudience"),
                "scenarios": payload.get("scenarios"),
                "tone_voice": payload.get("tone"),
                "forbidden_phrases": self._normalize_string_list(payload.get("forbiddenPhrases")),
                "cover_url": payload.get("coverUrl"),
            },
        )
        if not row:
            raise ContractError("品牌档案不存在", status_code=404)
        return {"brandId": str(row.id), "updatedAt": self._fmt_dt(row.updated_at)}

    def delete_product(self, *, owner_user_id: int, brand_id: int, operator_id: int) -> dict[str, Any]:
        ok = self.repository.soft_delete_product_cascade(
            owner_user_id=owner_user_id,
            brand_id=brand_id,
            operator_id=operator_id,
        )
        if not ok:
            raise ContractError("品牌档案不存在", status_code=404)
        return {"brandId": str(brand_id), "deletedAt": self._fmt_dt(datetime.now())}

    def list_selling_points(
        self,
        *,
        owner_user_id: int,
        brand_id: int,
        point_type: str | None,
        status: str | None,
        page_no: int,
        page_size: int,
    ) -> dict[str, Any]:
        if point_type and point_type not in SELLING_POINT_TYPES:
            raise ContractError("卖点类型不支持", status_code=400)
        if status and status not in SELLING_POINT_STATUSES:
            raise ContractError("卖点状态不支持", status_code=400)

        data = self.repository.list_selling_points(
            owner_user_id=owner_user_id,
            brand_id=brand_id,
            point_type=point_type,
            status=status,
            page_no=page_no,
            page_size=page_size,
        )
        return {
            "pageNo": page_no,
            "pageSize": page_size,
            "total": data["total"],
            "list": [self._map_selling_point(row) for row in data["list"]],
        }

    def save_selling_points(
        self,
        *,
        owner_user_id: int,
        brand_id: int,
        operator_id: int,
        upserts: list[dict[str, Any]],
        delete_ids: list[str],
    ) -> dict[str, int]:
        parsed_delete_ids = self._parse_id_list(delete_ids)
        normalized_upserts: list[dict[str, Any]] = []
        for item in upserts:
            point_type = item.get("type") or "optional"
            source = item.get("source") or "manual"
            status = item.get("status") or "draft"
            if point_type not in SELLING_POINT_TYPES:
                raise ContractError(f"卖点类型不支持: {point_type}", status_code=400)
            if source not in SELLING_POINT_SOURCES:
                raise ContractError(f"卖点来源不支持: {source}", status_code=400)
            if status not in SELLING_POINT_STATUSES:
                raise ContractError(f"卖点状态不支持: {status}", status_code=400)

            normalized_upserts.append(
                {
                    "id": item.get("id"),
                    "title": str(item["title"]).strip(),
                    "description": item.get("description"),
                    "type": point_type,
                    "weight": int(item.get("weight") or 5),
                    "source": source,
                    "status": status,
                    "platforms": self._normalize_string_list(item.get("platforms")),
                    "applicable_scenarios": self._normalize_string_list(item.get("scenarios")),
                }
            )

        return self.repository.upsert_selling_points(
            owner_user_id=owner_user_id,
            brand_id=brand_id,
            upserts=normalized_upserts,
            delete_ids=parsed_delete_ids,
            operator_id=operator_id,
        )

    def list_visual_assets(
        self,
        *,
        owner_user_id: int,
        brand_id: int,
        asset_type: str | None,
        page_no: int,
        page_size: int,
    ) -> dict[str, Any]:
        db_asset_type = None
        if asset_type:
            db_asset_type = ASSET_API_TO_DB.get(asset_type)
            if not db_asset_type:
                raise ContractError("素材类型不支持", status_code=400)

        data = self.repository.list_visual_assets(
            owner_user_id=owner_user_id,
            brand_id=brand_id,
            db_asset_type=db_asset_type,
            page_no=page_no,
            page_size=page_size,
        )
        return {
            "pageNo": page_no,
            "pageSize": page_size,
            "total": data["total"],
            "list": [self._map_visual_asset(row) for row in data["list"]],
        }

    def upload_visual_asset(
        self,
        *,
        owner_user_id: int,
        brand_id: int,
        operator_id: int,
        filename: str,
        content_type: str,
        file_bytes: bytes,
        asset_type: str,
        tags: list[str],
        platforms: list[str],
        scenarios: list[str],
        related_selling_point_ids: list[str],
        usable_for_cover: bool,
        usable_for_video: bool,
    ) -> dict[str, Any]:
        db_asset_type = ASSET_API_TO_DB.get(asset_type)
        if not db_asset_type:
            raise ContractError("素材类型不支持", status_code=400)
        if not file_bytes:
            raise ContractError("上传文件为空", status_code=400)

        ext = Path(filename).suffix or ""
        object_name = f"brand-assets/{owner_user_id}/{brand_id}/{uuid4().hex}{ext}"
        asset_url = self.storage_adapter.upload(object_name, file_bytes, content_type=content_type or "application/octet-stream")

        row = self.repository.create_visual_asset(
            owner_user_id=owner_user_id,
            brand_id=brand_id,
            operator_id=operator_id,
            payload={
                "asset_type": db_asset_type,
                "asset_url": asset_url,
                "thumbnail_url": asset_url,
                "tags": self._normalize_string_list(tags),
                "platforms": self._normalize_string_list(platforms),
                "applicable_scenarios": self._normalize_string_list(scenarios),
                "usable_for_cover": usable_for_cover,
                "usable_for_video": usable_for_video,
                "extra_data": {
                    "relatedSellingPointIds": self._normalize_string_list(related_selling_point_ids),
                    "originFileName": filename,
                    "contentType": content_type,
                    "size": len(file_bytes),
                },
            },
        )
        if not row:
            raise ContractError("品牌档案不存在", status_code=404)
        return {
            "id": str(row.id),
            "assetType": self._to_api_asset_type(row.asset_type),
            "assetUrl": row.asset_url,
            "thumbnail": row.thumbnail_url,
        }

    def update_visual_asset(
        self,
        *,
        owner_user_id: int,
        asset_id: int,
        operator_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        db_asset_type = None
        if payload.get("assetType"):
            db_asset_type = ASSET_API_TO_DB.get(payload["assetType"])
            if not db_asset_type:
                raise ContractError("素材类型不支持", status_code=400)

        row = self.repository.update_visual_asset(
            owner_user_id=owner_user_id,
            asset_id=asset_id,
            operator_id=operator_id,
            payload={
                "asset_type": db_asset_type,
                "tags": self._normalize_string_list(payload["tags"]) if "tags" in payload else None,
                "platforms": self._normalize_string_list(payload["platforms"]) if "platforms" in payload else None,
                "applicable_scenarios": self._normalize_string_list(payload["scenarios"]) if "scenarios" in payload else None,
                "related_selling_point_ids": self._normalize_string_list(payload["relatedSellingPointIds"]) if "relatedSellingPointIds" in payload else None,
                "usable_for_cover": payload.get("usableForCover"),
                "usable_for_video": payload.get("usableForVideo"),
            },
        )
        if not row:
            raise ContractError("素材不存在", status_code=404)
        return {"assetId": str(row.id), "updatedAt": self._fmt_dt(row.updated_at)}

    def delete_visual_asset(self, *, owner_user_id: int, asset_id: int, operator_id: int) -> dict[str, Any]:
        ok = self.repository.soft_delete_visual_asset(
            owner_user_id=owner_user_id,
            asset_id=asset_id,
            operator_id=operator_id,
        )
        if not ok:
            raise ContractError("素材不存在", status_code=404)
        return {"assetId": str(asset_id), "deletedAt": self._fmt_dt(datetime.now())}

    def build_context_payload(
        self,
        *,
        owner_user_id: int,
        brand_id: int,
        selling_point_ids: list[str],
        asset_ids: list[str],
        tone_rules: str | None,
    ) -> dict[str, Any]:
        product = self.repository.get_product_for_owner(owner_user_id=owner_user_id, brand_id=brand_id)
        if not product:
            raise ContractError("品牌档案不存在", status_code=404)

        parsed_sp_ids = self._parse_id_list(selling_point_ids)
        parsed_asset_ids = self._parse_id_list(asset_ids)

        points = self.repository.get_selling_points_by_ids(
            owner_user_id=owner_user_id,
            brand_id=brand_id,
            ids=parsed_sp_ids if parsed_sp_ids else None,
        )
        assets = self.repository.get_visual_assets_by_ids(
            owner_user_id=owner_user_id,
            brand_id=brand_id,
            ids=parsed_asset_ids if parsed_asset_ids else None,
        )

        required_points = [self._map_selling_point(p) for p in points if p.type == "required"]
        optional_points = [self._map_selling_point(p) for p in points if p.type == "optional"]

        return {
            "brandProfile": self._map_product(product),
            "requiredSellingPoints": required_points,
            "optionalSellingPoints": optional_points,
            "forbiddenPhrases": self._normalize_string_list(product.forbidden_phrases),
            "selectedAssets": [self._map_visual_asset(x) for x in assets],
            "toneRules": tone_rules or "",
        }

    @staticmethod
    def _normalize_string_list(values: list[str] | None) -> list[str]:
        if not values:
            return []
        seen: set[str] = set()
        normalized: list[str] = []
        for item in values:
            value = str(item).strip()
            if not value or value in seen:
                continue
            seen.add(value)
            normalized.append(value)
        return normalized

    @staticmethod
    def _parse_id_list(values: list[str] | None) -> list[int]:
        if not values:
            return []
        result: list[int] = []
        for raw in values:
            value = str(raw).strip()
            if not value:
                continue
            try:
                result.append(int(value))
            except ValueError as exc:
                raise ContractError(f"ID 非法: {value}", status_code=400) from exc
        return result

    @staticmethod
    def _fmt_dt(value: datetime | None) -> str | None:
        if not value:
            return None
        return value.strftime("%Y-%m-%d %H:%M:%S")

    def _map_product(self, row: BrandProduct) -> dict[str, Any]:
        return {
            "brandId": str(row.id),
            "brandName": row.brand_name,
            "productName": row.product_name,
            "positioning": row.positioning or "",
            "targetAudience": row.target_audience or "",
            "scenarios": row.scenarios or "",
            "tone": row.tone_voice or "",
            "forbiddenPhrases": self._normalize_string_list(row.forbidden_phrases),
            "coverUrl": row.cover_url,
            "createdAt": self._fmt_dt(row.created_at),
            "updatedAt": self._fmt_dt(row.updated_at),
        }

    def _map_selling_point(self, row: BrandSellingPoint) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "title": row.title,
            "description": row.description or "",
            "type": row.type,
            "weight": int(row.weight or 0),
            "source": row.source,
            "status": row.status,
            "platforms": self._normalize_string_list(row.platforms),
            "scenarios": self._normalize_string_list(row.applicable_scenarios),
            "createdAt": self._fmt_dt(row.created_at),
            "updatedAt": self._fmt_dt(row.updated_at),
        }

    def _map_visual_asset(self, row: BrandVisualAsset) -> dict[str, Any]:
        extra_data = row.extra_data if isinstance(row.extra_data, dict) else {}
        related = extra_data.get("relatedSellingPointIds")
        return {
            "id": str(row.id),
            "assetType": self._to_api_asset_type(row.asset_type),
            "assetUrl": row.asset_url,
            "thumbnail": row.thumbnail_url or row.asset_url,
            "tags": self._normalize_string_list(row.tags),
            "relatedSellingPointIds": self._normalize_string_list(related if isinstance(related, list) else []),
            "platforms": self._normalize_string_list(row.platforms),
            "scenarios": self._normalize_string_list(row.applicable_scenarios),
            "usableForCover": bool(row.usable_for_cover),
            "usableForVideo": bool(row.usable_for_video),
            "extraData": extra_data,
            "createdAt": self._fmt_dt(row.created_at),
            "updatedAt": self._fmt_dt(row.updated_at),
        }

    @staticmethod
    def _to_api_asset_type(db_asset_type: str) -> str:
        return ASSET_DB_TO_API.get(db_asset_type, "promo")
