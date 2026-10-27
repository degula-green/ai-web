from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ContractResponse(BaseModel):
    code: int
    msg: str
    data: Any = None


def contract_success(data: Any, *, msg: str = "查询成功", code: int = 200) -> dict[str, Any]:
    return {
        "code": code,
        "msg": msg,
        "data": data,
    }


def contract_error(msg: str, *, code: int) -> dict[str, Any]:
    return {
        "code": code,
        "msg": msg,
        "data": None,
    }
