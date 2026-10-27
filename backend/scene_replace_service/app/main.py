from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes_scene_replace import router as scene_replace_router
from app.core.config import get_settings
from app.core.logger import configure_logging
from app.schemas.response import ResponseModel


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()

    app = FastAPI(title=settings.app_name, debug=settings.debug)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "request failed"
        payload = ResponseModel(success=False, message=message, data=None)
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        payload = ResponseModel(success=False, message=f"internal server error: {exc}", data=None)
        return JSONResponse(status_code=500, content=payload.model_dump())

    app.mount("/outputs", StaticFiles(directory=settings.outputs_dir), name="outputs")
    app.mount("/uploads", StaticFiles(directory=settings.uploads_dir), name="uploads")
    app.include_router(scene_replace_router)
    return app


app = create_app()
