from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.brand_knowledge import BrandProduct, BrandSellingPoint, BrandVisualAsset


class BrandKnowledgeRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    @contextmanager
    def session_scope(self):
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def list_products(
        self,
        *,
        owner_user_id: int,
        keyword: str | None,
        page_no: int,
        page_size: int,
        sort_by: str,
    ) -> dict[str, Any]:
        with self.session_scope() as session:
            query = select(BrandProduct).where(
                BrandProduct.user_id == owner_user_id,
                BrandProduct.is_deleted == 0,
            )
            if keyword:
                like_kw = f"%{keyword.strip()}%"
                query = query.where(
                    or_(
                        BrandProduct.brand_name.like(like_kw),
                        BrandProduct.product_name.like(like_kw),
                    )
                )

            total = session.scalar(select(func.count()).select_from(query.subquery())) or 0

            if sort_by == "createdAt":
                query = query.order_by(desc(BrandProduct.created_at), desc(BrandProduct.id))
            else:
                query = query.order_by(desc(BrandProduct.updated_at), desc(BrandProduct.id))

            rows = session.scalars(query.offset((page_no - 1) * page_size).limit(page_size)).all()
            return {"total": int(total), "list": list(rows)}

    def create_product(
        self,
        *,
        owner_user_id: int,
        payload: dict[str, Any],
        operator_id: int,
    ) -> BrandProduct:
        with self.session_scope() as session:
            model = BrandProduct(
                user_id=owner_user_id,
                brand_name=payload["brand_name"],
                product_name=payload["product_name"],
                positioning=payload.get("positioning"),
                target_audience=payload.get("target_audience"),
                scenarios=payload.get("scenarios"),
                tone_voice=payload.get("tone_voice"),
                forbidden_phrases=payload.get("forbidden_phrases"),
                cover_url=payload.get("cover_url"),
                created_by=operator_id,
                updated_by=operator_id,
            )
            session.add(model)
            session.flush()
            session.refresh(model)
            return model

    def get_product_for_owner(self, *, owner_user_id: int, brand_id: int) -> BrandProduct | None:
        with self.session_scope() as session:
            return session.scalar(
                select(BrandProduct).where(
                    BrandProduct.id == brand_id,
                    BrandProduct.user_id == owner_user_id,
                    BrandProduct.is_deleted == 0,
                )
            )

    def update_product(
        self,
        *,
        owner_user_id: int,
        brand_id: int,
        payload: dict[str, Any],
        operator_id: int,
    ) -> BrandProduct | None:
        with self.session_scope() as session:
            model = session.scalar(
                select(BrandProduct).where(
                    BrandProduct.id == brand_id,
                    BrandProduct.user_id == owner_user_id,
                    BrandProduct.is_deleted == 0,
                )
            )
            if not model:
                return None

            model.brand_name = payload["brand_name"]
            model.product_name = payload["product_name"]
            model.positioning = payload.get("positioning")
            model.target_audience = payload.get("target_audience")
            model.scenarios = payload.get("scenarios")
            model.tone_voice = payload.get("tone_voice")
            model.forbidden_phrases = payload.get("forbidden_phrases")
            model.cover_url = payload.get("cover_url")
            model.updated_by = operator_id
            session.flush()
            session.refresh(model)
            return model

    def soft_delete_product_cascade(
        self,
        *,
        owner_user_id: int,
        brand_id: int,
        operator_id: int,
    ) -> bool:
        with self.session_scope() as session:
            product = session.scalar(
                select(BrandProduct).where(
                    BrandProduct.id == brand_id,
                    BrandProduct.user_id == owner_user_id,
                    BrandProduct.is_deleted == 0,
                )
            )
            if not product:
                return False

            product.is_deleted = 1
            product.updated_by = operator_id

            selling_points = session.scalars(
                select(BrandSellingPoint).where(
                    BrandSellingPoint.product_id == brand_id,
                    BrandSellingPoint.is_deleted == 0,
                )
            ).all()
            for point in selling_points:
                point.is_deleted = 1
                point.updated_by = operator_id

            assets = session.scalars(
                select(BrandVisualAsset).where(
                    BrandVisualAsset.product_id == brand_id,
                    BrandVisualAsset.is_deleted == 0,
                )
            ).all()
            for asset in assets:
                asset.is_deleted = 1
                asset.updated_by = operator_id
            return True

    def count_product_selling_points(self, *, product_ids: list[int]) -> dict[int, int]:
        if not product_ids:
            return {}
        with self.session_scope() as session:
            rows = session.execute(
                select(BrandSellingPoint.product_id, func.count(BrandSellingPoint.id))
                .where(
                    BrandSellingPoint.product_id.in_(product_ids),
                    BrandSellingPoint.is_deleted == 0,
                )
                .group_by(BrandSellingPoint.product_id)
            ).all()
            return {int(pid): int(cnt) for pid, cnt in rows}

    def count_product_visual_assets(self, *, product_ids: list[int]) -> dict[int, int]:
        if not product_ids:
            return {}
        with self.session_scope() as session:
            rows = session.execute(
                select(BrandVisualAsset.product_id, func.count(BrandVisualAsset.id))
                .where(
                    BrandVisualAsset.product_id.in_(product_ids),
                    BrandVisualAsset.is_deleted == 0,
                )
                .group_by(BrandVisualAsset.product_id)
            ).all()
            return {int(pid): int(cnt) for pid, cnt in rows}

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
        with self.session_scope() as session:
            query = (
                select(BrandSellingPoint)
                .join(BrandProduct, BrandProduct.id == BrandSellingPoint.product_id)
                .where(
                    BrandProduct.user_id == owner_user_id,
                    BrandProduct.id == brand_id,
                    BrandProduct.is_deleted == 0,
                    BrandSellingPoint.is_deleted == 0,
                )
            )
            if point_type:
                query = query.where(BrandSellingPoint.type == point_type)
            if status:
                query = query.where(BrandSellingPoint.status == status)

            total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
            rows = session.scalars(
                query.order_by(desc(BrandSellingPoint.updated_at), desc(BrandSellingPoint.id))
                .offset((page_no - 1) * page_size)
                .limit(page_size)
            ).all()
            return {"total": int(total), "list": list(rows)}

    def upsert_selling_points(
        self,
        *,
        owner_user_id: int,
        brand_id: int,
        upserts: list[dict[str, Any]],
        delete_ids: list[int],
        operator_id: int,
    ) -> dict[str, int]:
        with self.session_scope() as session:
            product = session.scalar(
                select(BrandProduct).where(
                    BrandProduct.id == brand_id,
                    BrandProduct.user_id == owner_user_id,
                    BrandProduct.is_deleted == 0,
                )
            )
            if not product:
                return {"upserted": 0, "deleted": 0}

            upserted = 0
            deleted = 0

            if delete_ids:
                delete_rows = session.scalars(
                    select(BrandSellingPoint).where(
                        BrandSellingPoint.product_id == brand_id,
                        BrandSellingPoint.id.in_(delete_ids),
                        BrandSellingPoint.is_deleted == 0,
                    )
                ).all()
                for row in delete_rows:
                    row.is_deleted = 1
                    row.updated_by = operator_id
                    deleted += 1

            for item in upserts:
                item_id = item.get("id")
                if item_id:
                    model = session.scalar(
                        select(BrandSellingPoint).where(
                            BrandSellingPoint.id == int(item_id),
                            BrandSellingPoint.product_id == brand_id,
                            BrandSellingPoint.is_deleted == 0,
                        )
                    )
                    if not model:
                        continue
                    model.title = item["title"]
                    model.description = item.get("description")
                    model.type = item.get("type") or "optional"
                    model.weight = int(item.get("weight") or 5)
                    model.source = item.get("source") or "manual"
                    model.status = item.get("status") or "draft"
                    model.platforms = item.get("platforms") or []
                    model.applicable_scenarios = item.get("applicable_scenarios") or []
                    model.updated_by = operator_id
                else:
                    model = BrandSellingPoint(
                        product_id=brand_id,
                        title=item["title"],
                        description=item.get("description"),
                        type=item.get("type") or "optional",
                        weight=int(item.get("weight") or 5),
                        source=item.get("source") or "manual",
                        status=item.get("status") or "draft",
                        platforms=item.get("platforms") or [],
                        applicable_scenarios=item.get("applicable_scenarios") or [],
                        created_by=operator_id,
                        updated_by=operator_id,
                    )
                    session.add(model)
                upserted += 1

            return {"upserted": upserted, "deleted": deleted}

    def list_visual_assets(
        self,
        *,
        owner_user_id: int,
        brand_id: int,
        db_asset_type: str | None,
        page_no: int,
        page_size: int,
    ) -> dict[str, Any]:
        with self.session_scope() as session:
            query = (
                select(BrandVisualAsset)
                .join(BrandProduct, BrandProduct.id == BrandVisualAsset.product_id)
                .where(
                    BrandProduct.user_id == owner_user_id,
                    BrandProduct.id == brand_id,
                    BrandProduct.is_deleted == 0,
                    BrandVisualAsset.is_deleted == 0,
                )
            )
            if db_asset_type:
                query = query.where(BrandVisualAsset.asset_type == db_asset_type)

            total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
            rows = session.scalars(
                query.order_by(desc(BrandVisualAsset.updated_at), desc(BrandVisualAsset.id))
                .offset((page_no - 1) * page_size)
                .limit(page_size)
            ).all()
            return {"total": int(total), "list": list(rows)}

    def create_visual_asset(
        self,
        *,
        owner_user_id: int,
        brand_id: int,
        payload: dict[str, Any],
        operator_id: int,
    ) -> BrandVisualAsset | None:
        with self.session_scope() as session:
            product = session.scalar(
                select(BrandProduct).where(
                    BrandProduct.id == brand_id,
                    BrandProduct.user_id == owner_user_id,
                    BrandProduct.is_deleted == 0,
                )
            )
            if not product:
                return None

            model = BrandVisualAsset(
                product_id=brand_id,
                asset_type=payload["asset_type"],
                asset_url=payload["asset_url"],
                thumbnail_url=payload.get("thumbnail_url"),
                tags=payload.get("tags") or [],
                platforms=payload.get("platforms") or [],
                applicable_scenarios=payload.get("applicable_scenarios") or [],
                usable_for_cover=1 if payload.get("usable_for_cover") else 0,
                usable_for_video=1 if payload.get("usable_for_video") else 0,
                extra_data=payload.get("extra_data") or {},
                created_by=operator_id,
                updated_by=operator_id,
            )
            session.add(model)
            session.flush()
            session.refresh(model)
            return model

    def get_visual_asset_for_owner(self, *, owner_user_id: int, asset_id: int) -> BrandVisualAsset | None:
        with self.session_scope() as session:
            return session.scalar(
                select(BrandVisualAsset)
                .join(BrandProduct, BrandProduct.id == BrandVisualAsset.product_id)
                .where(
                    BrandVisualAsset.id == asset_id,
                    BrandVisualAsset.is_deleted == 0,
                    BrandProduct.user_id == owner_user_id,
                    BrandProduct.is_deleted == 0,
                )
            )

    def update_visual_asset(
        self,
        *,
        owner_user_id: int,
        asset_id: int,
        payload: dict[str, Any],
        operator_id: int,
    ) -> BrandVisualAsset | None:
        with self.session_scope() as session:
            model = session.scalar(
                select(BrandVisualAsset)
                .join(BrandProduct, BrandProduct.id == BrandVisualAsset.product_id)
                .where(
                    BrandVisualAsset.id == asset_id,
                    BrandVisualAsset.is_deleted == 0,
                    BrandProduct.user_id == owner_user_id,
                    BrandProduct.is_deleted == 0,
                )
            )
            if not model:
                return None

            if "asset_type" in payload and payload["asset_type"]:
                model.asset_type = payload["asset_type"]
            if "tags" in payload:
                model.tags = payload["tags"] or []
            if "platforms" in payload:
                model.platforms = payload["platforms"] or []
            if "applicable_scenarios" in payload:
                model.applicable_scenarios = payload["applicable_scenarios"] or []
            if "usable_for_cover" in payload:
                model.usable_for_cover = 1 if payload["usable_for_cover"] else 0
            if "usable_for_video" in payload:
                model.usable_for_video = 1 if payload["usable_for_video"] else 0

            extra_data = dict(model.extra_data or {})
            if "related_selling_point_ids" in payload:
                extra_data["relatedSellingPointIds"] = payload["related_selling_point_ids"] or []
            model.extra_data = extra_data
            model.updated_by = operator_id

            session.flush()
            session.refresh(model)
            return model

    def soft_delete_visual_asset(self, *, owner_user_id: int, asset_id: int, operator_id: int) -> bool:
        with self.session_scope() as session:
            model = session.scalar(
                select(BrandVisualAsset)
                .join(BrandProduct, BrandProduct.id == BrandVisualAsset.product_id)
                .where(
                    BrandVisualAsset.id == asset_id,
                    BrandVisualAsset.is_deleted == 0,
                    BrandProduct.user_id == owner_user_id,
                    BrandProduct.is_deleted == 0,
                )
            )
            if not model:
                return False
            model.is_deleted = 1
            model.updated_by = operator_id
            return True

    def get_selling_points_by_ids(
        self,
        *,
        owner_user_id: int,
        brand_id: int,
        ids: list[int] | None,
    ) -> list[BrandSellingPoint]:
        with self.session_scope() as session:
            filters = [
                BrandSellingPoint.product_id == brand_id,
                BrandSellingPoint.is_deleted == 0,
                BrandProduct.id == brand_id,
                BrandProduct.user_id == owner_user_id,
                BrandProduct.is_deleted == 0,
            ]
            if ids:
                filters.append(BrandSellingPoint.id.in_(ids))
            query = (
                select(BrandSellingPoint)
                .join(BrandProduct, BrandProduct.id == BrandSellingPoint.product_id)
                .where(and_(*filters))
                .order_by(desc(BrandSellingPoint.weight), BrandSellingPoint.id.asc())
            )
            return list(session.scalars(query).all())

    def get_visual_assets_by_ids(
        self,
        *,
        owner_user_id: int,
        brand_id: int,
        ids: list[int] | None,
    ) -> list[BrandVisualAsset]:
        with self.session_scope() as session:
            filters = [
                BrandVisualAsset.product_id == brand_id,
                BrandVisualAsset.is_deleted == 0,
                BrandProduct.id == brand_id,
                BrandProduct.user_id == owner_user_id,
                BrandProduct.is_deleted == 0,
            ]
            if ids:
                filters.append(BrandVisualAsset.id.in_(ids))
            query = (
                select(BrandVisualAsset)
                .join(BrandProduct, BrandProduct.id == BrandVisualAsset.product_id)
                .where(and_(*filters))
                .order_by(desc(BrandVisualAsset.updated_at), desc(BrandVisualAsset.id))
            )
            return list(session.scalars(query).all())
