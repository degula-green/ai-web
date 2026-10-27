from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2


@dataclass(slots=True)
class VideoMetadata:
    width: int
    height: int
    fps: float
    frame_count: int
    duration_seconds: float


def get_video_metadata(video_path: Path) -> VideoMetadata:
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError(f"failed to open video: {video_path}")

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    capture.release()

    safe_fps = fps if fps > 0 else 25.0
    duration_seconds = frame_count / safe_fps if frame_count > 0 else 0.0
    return VideoMetadata(
        width=width,
        height=height,
        fps=safe_fps,
        frame_count=frame_count,
        duration_seconds=duration_seconds,
    )
