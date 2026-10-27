from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

# Windows asyncio workaround for Playwright subprocesses
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.contract import contract_error
from app.core.exceptions import AppError, ContractError
from app.core.lifecycle import lifespan
from app.core.logging import configure_logging
from app.core.response import ResponseEnvelope

logger = logging.getLogger(__name__)


def _apply_cors_headers(response: JSONResponse, request: Request, allowed_origins: list[str]) -> JSONResponse:
    origin = request.headers.get("origin")
    if not origin:
        return response
    if "*" in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
    elif origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        return response
    response.headers["Vary"] = "Origin"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.logging)
    app = FastAPI(title=settings.app.name, debug=settings.app.debug, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        if request.url.path.startswith("/api/v1/auth") or request.url.path.startswith("/api/v1/iam"):
            response = JSONResponse(status_code=exc.status_code, content=contract_error(exc.message, code=exc.status_code))
            return _apply_cors_headers(response, request, settings.app.allowed_origins)
        payload = ResponseEnvelope[dict](success=False, code=exc.code, message=exc.message, data=None)
        response = JSONResponse(status_code=exc.status_code, content=payload.model_dump())
        return _apply_cors_headers(response, request, settings.app.allowed_origins)

    @app.exception_handler(ContractError)
    async def handle_contract_error(request: Request, exc: ContractError) -> JSONResponse:
        response = JSONResponse(status_code=exc.status_code, content=contract_error(exc.message, code=exc.status_code))
        return _apply_cors_headers(response, request, settings.app.allowed_origins)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception for %s %s", request.method, request.url.path)
        payload = ResponseEnvelope[dict](success=False, code=500, message=str(exc) or "Internal Server Error", data=None)
        response = JSONResponse(status_code=500, content=payload.model_dump())
        return _apply_cors_headers(response, request, settings.app.allowed_origins)

    app.include_router(api_router, prefix=settings.app.api_prefix)
    return app


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        reload_dirs=["."],
        reload_excludes=[
            "runtime/*",
            "runtime/**/*",
            "exports/*",
            "exports/**/*",
            "**/__pycache__/*",
        ],
        log_level="info",
    )
