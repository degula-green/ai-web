from __future__ import annotations

from pydantic import BaseModel, Field


class AssetUploadTicketRequest(BaseModel):
    module: str = Field(..., description="业务模块，例如 voice_clone / digital_human")
    media_type: str = Field(..., description="文件类型：audio / image / video")
    file_name: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., min_length=1, max_length=255)
    draft_id: str | None = Field(default=None, max_length=64)


class AssetUploadTicketRead(BaseModel):
    module: str
    media_type: str
    object_name: str
    upload_method: str = "PUT"
    upload_url: str
    file_url: str
    content_type: str
    expires_in_seconds: int = 900
