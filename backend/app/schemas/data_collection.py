from __future__ import annotations

from pydantic import BaseModel, Field


class KeywordTaskCreateRequest(BaseModel):
    platformCode: str = "douyin"
    authAccountId: int = Field(..., ge=1)
    keyword: str
    contentKind: str = "image"
    timeRange: str | None = "24h"
    sortBy: str | None = "heat"
    pageSize: int = Field(default=20, ge=1, le=100)


class MaterialImportRequest(BaseModel):
    platformCode: str = "douyin"
    contentKind: str
    sourceScene: str
    sourceRefNo: str
    contentIds: list[str] = Field(default_factory=list)


class ExportRequest(BaseModel):
    exportScope: str
    contentKind: str | None = None
    fileType: str = "csv"
    sourceRefNo: str | None = None
    boardType: str | None = "hot"
    snapshotNo: str | None = None
