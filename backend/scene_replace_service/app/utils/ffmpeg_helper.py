from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)


def run_ffmpeg(command: list[str]) -> None:
    logger.info("running ffmpeg command: %s", " ".join(shlex.quote(part) for part in command))
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        logger.error("ffmpeg failed: %s", completed.stderr.strip())
        raise RuntimeError(f"ffmpeg command failed: {completed.stderr.strip()}")


def mux_video_with_source_audio(rendered_video: Path, source_video: Path, output_video: Path) -> None:
    settings = get_settings()
    command = [
        settings.ffmpeg_bin,
        "-y",
        "-i",
        str(rendered_video),
        "-i",
        str(source_video),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0?",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        str(output_video),
    ]
    run_ffmpeg(command)
