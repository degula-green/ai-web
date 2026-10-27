from __future__ import annotations

from pydantic import BaseModel, Field


class BrandProductUpsertRequest(BaseModel):
    brandName: str = Field(min_length=1, max_length=64)
    productName: str = Field(min_length=1, max_length=128)
    positioning: str | None = None
    targetAudience: str | None = None
    scenarios: str | None = None
    tone: str | None = None
    forbiddenPhrases: list[str] = Field(default_factory=list)
    coverUrl: str | None = None


class SellingPointUpsertItem(BaseModel):
    id: str | None = None
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    type: str = "optional"
    weight: int = Field(default=5, ge=0, le=10)
    source: str = "manual"
    status: str = "draft"
    platforms: list[str] = Field(default_factory=list)
    scenarios: list[str] = Field(default_factory=list)


class SellingPointsSaveRequest(BaseModel):
    upserts: list[SellingPointUpsertItem] = Field(default_factory=list)
    deleteIds: list[str] = Field(default_factory=list)


class VisualAssetUpdateRequest(BaseModel):
    assetType: str | None = None
    tags: list[str] | None = None
    platforms: list[str] | None = None
    scenarios: list[str] | None = None
    relatedSellingPointIds: list[str] | None = None
    usableForCover: bool | None = None
    usableForVideo: bool | None = None


class BuildContextPayloadRequest(BaseModel):
    brandId: str
    sellingPointIds: list[str] = Field(default_factory=list)
    assetIds: list[str] = Field(default_factory=list)
    toneRules: str | None = None
