from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ResponseModel(BaseModel):
    success: bool
    message: str
    data: Any | None = None


class SceneReplaceResponseData(BaseModel):
    task_id: str
    output_video: str
