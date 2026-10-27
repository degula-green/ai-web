from __future__ import annotations

import traceback
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas.response import ResponseModel, SceneReplaceResponseData
from app.services.compose_service import ComposeService
from app.services.file_service import FileService
from app.services.matting_service import MattingService

router = APIRouter()

file_service = FileService()
matting_service = MattingService()
compose_service = ComposeService()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/v1/scene-replace", response_model=ResponseModel)
async def scene_replace(
    source_video: UploadFile = File(...),
    background_image: UploadFile | None = File(default=None),
    background_video: UploadFile | None = File(default=None),
    background_image_url: str | None = Form(default=None),
    background_video_url: str | None = Form(default=None),
    output_width: int = Form(default=1080),
    output_height: int = Form(default=1920),
) -> ResponseModel:
    task_id = uuid.uuid4().hex
    try:
        source_video_path = await file_service.save_upload(source_video, prefix=f"{task_id}_source")
        background_image_path: Path | None = None
        background_video_path: Path | None = None
        if background_image is not None:
            background_image_path = await file_service.save_upload(background_image, prefix=f"{task_id}_background")
        elif background_image_url:
            background_image_path = file_service.download_file(
                background_image_url,
                prefix=f"{task_id}_background",
                default_suffix=".jpg",
            )
        elif background_video is not None:
            background_video_path = await file_service.save_upload(background_video, prefix=f"{task_id}_background")
        elif background_video_url:
            background_video_path = file_service.download_file(
                background_video_url,
                prefix=f"{task_id}_background",
                default_suffix=".mp4",
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="background_image/background_image_url or background_video/background_video_url is required",
            )
        workspace = file_service.create_task_workspace(task_id)
        output_video_path = file_service.build_output_path(task_id)

        matting_result = matting_service.process_video(source_video_path, workspace["matting"])
        compose_result = compose_service.compose(
            matting_result=matting_result,
            background_image=background_image_path,
            background_video=background_video_path,
            source_video=source_video_path,
            output_video=output_video_path,
            output_width=output_width,
            output_height=output_height,
        )
        output_relative = Path("outputs") / compose_result.output_video.name
        return ResponseModel(
            success=True,
            message="scene replaced successfully",
            data=SceneReplaceResponseData(task_id=task_id, output_video=output_relative.as_posix()).model_dump(),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"scene replace failed: {exc}") from exc
