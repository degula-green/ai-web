from __future__ import annotations

from uuid import uuid4


def generate_id(prefix: str | None = None) -> str:
    value = uuid4().hex
    return f"{prefix}_{value}" if prefix else value
