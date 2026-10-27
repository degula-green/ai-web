from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BrandProduct(Base):
    __tablename__ = "brand_products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    brand_name: Mapped[str] = mapped_column(String(64))
    product_name: Mapped[str] = mapped_column(String(128))
    positioning: Mapped[str | None] = mapped_column(Text)
    target_audience: Mapped[str | None] = mapped_column(Text)
    scenarios: Mapped[str | None] = mapped_column(Text)
    tone_voice: Mapped[str | None] = mapped_column(String(255))
    forbidden_phrases: Mapped[list[str] | None] = mapped_column(JSON)
    cover_url: Mapped[str | None] = mapped_column(String(512))
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int] = mapped_column(BigInteger, default=0)
    updated_by: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class BrandSellingPoint(Base):
    __tablename__ = "brand_selling_points"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(BigInteger, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(32), default="optional")
    weight: Mapped[int] = mapped_column(Integer, default=5)
    source: Mapped[str] = mapped_column(String(32), default="manual")
    status: Mapped[str] = mapped_column(String(32), default="confirmed")
    platforms: Mapped[list[str] | None] = mapped_column(JSON)
    applicable_scenarios: Mapped[list[str] | None] = mapped_column(JSON)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int] = mapped_column(BigInteger, default=0)
    updated_by: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class BrandVisualAsset(Base):
    __tablename__ = "brand_visual_assets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(BigInteger, index=True)
    asset_type: Mapped[str] = mapped_column(String(32))
    asset_url: Mapped[str] = mapped_column(String(512))
    thumbnail_url: Mapped[str | None] = mapped_column(String(512))
    tags: Mapped[list[str] | None] = mapped_column(JSON)
    platforms: Mapped[list[str] | None] = mapped_column(JSON)
    applicable_scenarios: Mapped[list[str] | None] = mapped_column(JSON)
    usable_for_cover: Mapped[int] = mapped_column(Integer, default=0)
    usable_for_video: Mapped[int] = mapped_column(Integer, default=0)
    extra_data: Mapped[dict | None] = mapped_column(JSON)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int] = mapped_column(BigInteger, default=0)
    updated_by: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
