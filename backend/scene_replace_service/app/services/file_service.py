from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from fastapi import UploadFile

from app.core.config import get_settings


class FileService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def ensure_directories(self) -> None:
        self.settings.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.settings.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.settings.temp_dir.mkdir(parents=True, exist_ok=True)

    def create_task_workspace(self, task_id: str) -> dict[str, Path]:
        base_dir = self.settings.temp_dir / task_id
        workspace = {
            "base": base_dir,
            "matting": base_dir / "matting",
        }
        for path in workspace.values():
            path.mkdir(parents=True, exist_ok=True)
        return workspace

    async def save_upload(self, upload_file: UploadFile, prefix: str) -> Path:
        self.ensure_directories()
        suffix = Path(upload_file.filename or "").suffix or ".bin"
        file_name = f"{prefix}_{uuid.uuid4().hex}{suffix}"
        destination = self.settings.uploads_dir / file_name
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        await upload_file.close()
        return destination

    def download_file(self, file_url: str, prefix: str, default_suffix: str = ".bin") -> Path:
        self.ensure_directories()
        request = Request(file_url, headers={"User-Agent": "scene_replace_service/1.0"})
        with urlopen(request, timeout=300) as response:
            content_type = response.headers.get_content_type()
            suffix = self._guess_suffix(file_url=file_url, content_type=content_type, default_suffix=default_suffix)
            destination = self.settings.uploads_dir / f"{prefix}_{uuid.uuid4().hex}{suffix}"
            with destination.open("wb") as output_file:
                shutil.copyfileobj(response, output_file)
        return destination

    def build_output_path(self, task_id: str) -> Path:
        self.ensure_directories()
        return self.settings.outputs_dir / f"{task_id}.mp4"

    @staticmethod
    def _guess_suffix(file_url: str, content_type: str | None, default_suffix: str) -> str:
        suffix = Path(urlparse(file_url).path).suffix
        if suffix:
            return suffix

        mapping = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "video/mp4": ".mp4",
        }
        return mapping.get((content_type or "").lower(), default_suffix)
