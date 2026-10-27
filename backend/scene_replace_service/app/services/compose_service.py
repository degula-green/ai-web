from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.core.logger import get_logger
from app.services.matting_service import MattingResult
from app.utils.ffmpeg_helper import mux_video_with_source_audio

logger = get_logger(__name__)


@dataclass(slots=True)
class ComposeResult:
    output_video: Path


class ComposeService:
    def compose(
        self,
        matting_result: MattingResult,
        background_image: Path | None,
        background_video: Path | None,
        source_video: Path,
        output_video: Path,
        output_width: int,
        output_height: int,
    ) -> ComposeResult:
        background = None
        background_capture = None
        if background_image is not None:
            background = self._imread(background_image, cv2.IMREAD_COLOR)
            if background is None:
                raise ValueError(f"failed to load background image: {background_image}")
            background = self._resize_background_cover(background, output_width, output_height)
        elif background_video is not None:
            background_capture = cv2.VideoCapture(str(background_video))
            if not background_capture.isOpened():
                raise ValueError(f"failed to open background video: {background_video}")
        else:
            raise ValueError("background_image or background_video is required")

        frame_paths = sorted(matting_result.foreground_dir.glob("*.png"))
        alpha_paths = sorted(matting_result.alpha_dir.glob("*.png"))
        if not frame_paths or len(frame_paths) != len(alpha_paths):
            raise ValueError("matting frame output is incomplete")

        temp_video = output_video.with_name(f"{output_video.stem}_silent.mp4")
        writer = cv2.VideoWriter(
            str(temp_video),
            cv2.VideoWriter_fourcc(*"mp4v"),
            matting_result.metadata.fps,
            (output_width, output_height),
        )
        if not writer.isOpened():
            raise RuntimeError(f"failed to create output video writer: {temp_video}")

        try:
            for foreground_path, alpha_path in zip(frame_paths, alpha_paths, strict=True):
                foreground = self._imread(foreground_path, cv2.IMREAD_COLOR)
                alpha = self._imread(alpha_path, cv2.IMREAD_GRAYSCALE)
                current_background = background
                if background_capture is not None:
                    current_background = self._read_background_frame(background_capture, output_width, output_height)
                composed = self._compose_single_frame(
                    current_background,
                    foreground,
                    alpha,
                    output_width,
                    output_height,
                )
                writer.write(composed)
        finally:
            writer.release()
            if background_capture is not None:
                background_capture.release()

        mux_video_with_source_audio(temp_video, source_video, output_video)
        if temp_video.exists():
            temp_video.unlink()
        logger.info("composition completed: %s", output_video)
        return ComposeResult(output_video=output_video)

    def _compose_single_frame(
        self,
        background: np.ndarray,
        foreground: np.ndarray,
        alpha: np.ndarray,
        output_width: int,
        output_height: int,
    ) -> np.ndarray:
        background_frame = self._fit_frame(background, output_width, output_height)
        foreground_frame = self._fit_frame(foreground, output_width, output_height)
        alpha_frame = self._fit_mask(alpha, output_width, output_height)

        if np.count_nonzero(alpha_frame > 12) == 0:
            return background_frame

        alpha_soft = self._soften_alpha(alpha_frame)
        alpha_float = np.clip(alpha_soft.astype(np.float32) / 255.0, 0.0, 1.0)[..., None]

        canvas = background_frame.astype(np.float32)
        foreground_float = foreground_frame.astype(np.float32)
        shadow = self._build_shadow(alpha_soft)
        canvas = shadow + canvas * (1.0 - np.clip(shadow / 255.0, 0.0, 1.0))
        blended = foreground_float * alpha_float + canvas * (1.0 - alpha_float)
        blended = self._match_foreground_tone(blended, foreground_float, alpha_float)
        canvas = np.where(alpha_float > 0.0, blended, canvas)
        canvas = np.clip(canvas, 0.0, 255.0)
        canvas = self._feather_edge(canvas.astype(np.uint8), background_frame, alpha_soft)
        return canvas.astype(np.uint8)

    @staticmethod
    def _extract_bbox(alpha: np.ndarray, threshold: int = 12) -> tuple[int, int, int, int] | None:
        coords = cv2.findNonZero((alpha > threshold).astype(np.uint8))
        if coords is None:
            return None
        x, y, width, height = cv2.boundingRect(coords)
        return x, y, width, height

    @staticmethod
    def _resize_background_cover(image: np.ndarray, output_width: int, output_height: int) -> np.ndarray:
        src_height, src_width = image.shape[:2]
        scale = max(output_width / src_width, output_height / src_height)
        resized = cv2.resize(
            image,
            (max(1, int(src_width * scale)), max(1, int(src_height * scale))),
            interpolation=cv2.INTER_LINEAR,
        )
        y = max(0, (resized.shape[0] - output_height) // 2)
        x = max(0, (resized.shape[1] - output_width) // 2)
        return resized[y : y + output_height, x : x + output_width].copy()

    @staticmethod
    def _fit_frame(image: np.ndarray, output_width: int, output_height: int) -> np.ndarray:
        if image.shape[1] == output_width and image.shape[0] == output_height:
            return image.copy()
        return cv2.resize(image, (output_width, output_height), interpolation=cv2.INTER_LINEAR)

    @staticmethod
    def _fit_mask(mask: np.ndarray, output_width: int, output_height: int) -> np.ndarray:
        if mask.shape[1] == output_width and mask.shape[0] == output_height:
            return mask.copy()
        return cv2.resize(mask, (output_width, output_height), interpolation=cv2.INTER_LINEAR)

    @staticmethod
    def _imread(path: Path, flags: int) -> np.ndarray | None:
        if not path.exists():
            return None
        data = np.fromfile(str(path), dtype=np.uint8)
        if data.size == 0:
            return None
        return cv2.imdecode(data, flags)

    def _read_background_frame(self, capture: cv2.VideoCapture, output_width: int, output_height: int) -> np.ndarray:
        ok, frame = capture.read()
        if not ok:
            capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = capture.read()
        if not ok or frame is None:
            raise ValueError("failed to read frame from background video")
        return self._resize_background_cover(frame, output_width, output_height)

    @staticmethod
    def _soften_alpha(alpha: np.ndarray) -> np.ndarray:
        alpha = cv2.GaussianBlur(alpha, (0, 0), sigmaX=1.2, sigmaY=1.2)
        return np.clip(alpha, 0, 255).astype(np.uint8)

    @staticmethod
    def _build_shadow(alpha: np.ndarray) -> np.ndarray:
        shadow_mask = cv2.GaussianBlur(alpha, (0, 0), sigmaX=10.0, sigmaY=10.0).astype(np.float32) / 255.0
        shadow_mask *= 0.18
        shadow_mask = np.roll(shadow_mask, shift=8, axis=0)
        shadow_mask = np.roll(shadow_mask, shift=4, axis=1)
        shadow_mask[:8, :] = 0
        shadow_mask[:, :4] = 0
        shadow = np.zeros((alpha.shape[0], alpha.shape[1], 3), dtype=np.float32)
        shadow[:] = 20.0
        return shadow * shadow_mask[..., None]

    @staticmethod
    def _match_foreground_tone(blended: np.ndarray, foreground: np.ndarray, alpha: np.ndarray) -> np.ndarray:
        active = alpha[..., 0] > 0.02
        if not np.any(active):
            return blended
        result = blended.copy()
        fg_values = foreground[active]
        if fg_values.size == 0:
            return result
        mean_bgr = fg_values.mean(axis=0)
        gain = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        if mean_bgr[1] > mean_bgr[2] * 1.15:
            gain = np.array([1.03, 0.96, 1.04], dtype=np.float32)
        elif mean_bgr[2] > mean_bgr[1] * 1.15:
            gain = np.array([1.04, 1.02, 0.97], dtype=np.float32)
        result[active] = np.clip(result[active] * gain, 0.0, 255.0)
        return result

    @staticmethod
    def _feather_edge(composed: np.ndarray, background: np.ndarray, alpha: np.ndarray) -> np.ndarray:
        edge = cv2.Canny(alpha, 32, 96)
        if np.count_nonzero(edge) == 0:
            return composed
        edge = cv2.GaussianBlur(edge, (0, 0), sigmaX=1.5, sigmaY=1.5).astype(np.float32) / 255.0
        edge = edge[..., None] * 0.35
        feathered = composed.astype(np.float32) * (1.0 - edge) + background.astype(np.float32) * edge
        return np.clip(feathered, 0.0, 255.0).astype(np.uint8)
