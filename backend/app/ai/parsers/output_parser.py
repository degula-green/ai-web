from __future__ import annotations

import json
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseStructuredOutputParser(Generic[T]):
    def __init__(self, model_type: type[T]) -> None:
        self.model_type = model_type

    def parse(self, payload: str | dict) -> T:
        if isinstance(payload, dict):
            return self.model_type.model_validate(payload)
        stripped = payload.strip()
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            start = stripped.find("{")
            end = stripped.rfind("}")
            if start >= 0 and end > start:
                data = json.loads(stripped[start : end + 1])
            else:
                raise
        return self.model_type.model_validate(data)
