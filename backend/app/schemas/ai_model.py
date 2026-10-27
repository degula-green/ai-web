from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AIProviderTestRequest(BaseModel):
    providerCode: str = Field(min_length=2, max_length=32)
    providerName: str = Field(min_length=2, max_length=64)
    baseUrl: str = Field(min_length=8, max_length=255)
    apiKey: str = Field(min_length=10, max_length=255)
    modelName: str = Field(min_length=2, max_length=128)
    timeoutSeconds: int = Field(default=60, ge=5, le=300)


class AIProviderUpsertRequest(AIProviderTestRequest):
    isEnabled: bool = True
    extraConfig: dict | None = None


class AITokenUsageLogCreateRequest(BaseModel):
    taskId: str | None = Field(default=None, max_length=64)
    scene: str = Field(min_length=2, max_length=64)
    providerCode: str = Field(min_length=2, max_length=32)
    modelName: str = Field(min_length=2, max_length=128)
    inputTokens: int = Field(default=0, ge=0)
    outputTokens: int = Field(default=0, ge=0)
    cachedTokens: int = Field(default=0, ge=0)
    estimatedCost: float = Field(default=0.0, ge=0.0)
    currency: str = Field(default="CNY", min_length=3, max_length=16)
    requestId: str | None = Field(default=None, max_length=128)
    remark: str | None = None
    metadata: dict | None = None


class AIProviderConfigView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    providerCode: str
    providerName: str
    baseUrl: str
    defaultModel: str
    isEnabled: bool
    timeoutSeconds: int
    lastTestStatus: str | None
    lastTestMessage: str | None
    lastTestAt: datetime | None
    createdAt: datetime
    updatedAt: datetime


class AIProviderTestResult(BaseModel):
    ok: bool
    message: str
    latencyMs: int
    model: str


class AITokenUsageSummaryView(BaseModel):
    userId: int
    inputTokens: int
    outputTokens: int
    cachedTokens: int
    totalTokens: int
    estimatedCost: float
    records: int
