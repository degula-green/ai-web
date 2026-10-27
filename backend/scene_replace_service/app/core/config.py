from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "scene_replace_service"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True
    api_prefix: str = "/api/v1"

    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2])
    uploads_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2] / "uploads")
    outputs_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2] / "outputs")
    temp_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2] / "temp")
    model_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2] / "models")
    rvm_checkpoint: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2] / "models" / "rvm_mobilenetv3.pth"
    )
    rvm_variant: str = "mobilenetv3"
    ffmpeg_bin: str = "ffmpeg"
    ffprobe_bin: str = "ffprobe"
    max_upload_size_mb: int = 512

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="SCENE_REPLACE_",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.outputs_dir.mkdir(parents=True, exist_ok=True)
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    settings.model_dir.mkdir(parents=True, exist_ok=True)
    return settings
