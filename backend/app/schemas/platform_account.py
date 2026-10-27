from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AccountShortInfo(BaseModel):
    accountId: int
    platformCode: str
    accountName: str
    nickname: Optional[str] = None
    avatarUrl: Optional[str] = None
    platformUid: Optional[str] = None
    authStatus: str
    accountStatus: Optional[str] = None
    identityType: Optional[str] = None
    identityValue: Optional[str] = None
    secUserId: Optional[str] = None
    authType: Optional[str] = None
    sessionStatus: Optional[str] = None
    expiresAt: Optional[datetime] = None
    lastSyncAt: Optional[datetime] = None
    lastValidatedAt: Optional[datetime] = None
    lastRefreshAt: Optional[datetime] = None
    lastIdentityVerifiedAt: Optional[datetime] = None
    lastIdentityError: Optional[str] = None
    validatedIdentity: Optional[str] = None
    lastValidationError: Optional[str] = None
    cookieVersion: Optional[int] = None
    updatedAt: Optional[datetime] = None


class AccountListResponse(BaseModel):
    list: List[AccountShortInfo]
    total: int


class AccountDetailResponse(BaseModel):
    id: int
    platformCode: str
    accountName: str
    nickname: Optional[str] = None
    avatarUrl: Optional[str] = None
    authStatus: str
    tags: Optional[Dict[str, Any]] = None
    remark: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime


class UnbindResponse(BaseModel):
    accountId: int
    unbindAt: datetime


class AuthHistoryItem(BaseModel):
    id: int
    platformCode: str
    accountName: Optional[str] = None
    eventType: str = Field(..., description="bind/refresh/expire/revoke")
    eventStatus: str = Field(..., description="success/failed")
    failReason: Optional[str] = None
    extraData: Optional[Dict[str, Any]] = None
    createdAt: datetime


class AuthHistoryResponse(BaseModel):
    list: List[AuthHistoryItem]
    total: int


class CookieBridgeBindRequest(BaseModel):
    platformCode: str
    clientId: str
    setDefault: bool = True


class CookieBridgeClientInfo(BaseModel):
    clientId: str
    connected: bool
    nicknames: Dict[str, str] = Field(default_factory=dict)
    platforms: Dict[str, Any] = Field(default_factory=dict)
    connectedAt: Optional[float] = None
    lastSeen: Optional[float] = None


class CookieBridgeAccountsResponse(BaseModel):
    list: List[CookieBridgeClientInfo]
    total: int
    bridgeUrl: str


class CookieBridgeBindResponse(BaseModel):
    accountId: int
    crawlerCookieAccountId: int
    bridgeClientId: str
    platformCode: str
    syncedAt: datetime


class SyncAccountWorksRequest(BaseModel):
    maxCount: int = Field(50, ge=1, le=500, description="Maximum number of works to sync")


class SyncAccountWorksResponse(BaseModel):
    accountId: int
    platformCode: str
    secUserId: str
    syncedCount: int
    relationCount: int
    duplicatedCount: int
    creatorSaved: bool = False
    awemeIds: List[str] = Field(default_factory=list)
