from __future__ import annotations

from datetime import datetime, timezone
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from app.core.security import generate_request_id

T = TypeVar("T")


class ResponseEnvelope(BaseModel, Generic[T]):
    success: bool = True
    code: int = 200
    message: str = "success"
    request_id: str = Field(default_factory=generate_request_id)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: T | None = None


def success_response(data: T, *, message: str = "success", code: int = 200) -> ResponseEnvelope[T]:
    return ResponseEnvelope[T](success=True, code=code, message=message, data=data)


def doc_response(data: object | None, *, message: str, code: int = 200) -> dict[str, object | None]:
    return {"code": code, "msg": message, "data": data}
