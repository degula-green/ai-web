from __future__ import annotations

from typing import Generic, TypeVar

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

T = TypeVar("T")


class ContractEnvelope(BaseModel, Generic[T]):
    code: int
    msg: str
    data: T | None = None


class ContractError(Exception):
    def __init__(self, status_code: int, msg: str) -> None:
        super().__init__(msg)
        self.status_code = status_code
        self.msg = msg


def contract_response(data: T | None, *, msg: str, status_code: int = 200) -> JSONResponse:
    payload = ContractEnvelope[T](code=status_code, msg=msg, data=data)
    return JSONResponse(status_code=status_code, content=jsonable_encoder(payload))

