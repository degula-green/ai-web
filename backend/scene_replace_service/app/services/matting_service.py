from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import torch

from app.core.config import get_settings
from app.core.logger import get_logger
from app.utils.video_helper import VideoMetadata, get_video_metadata

logger = get_logger(__name__)


@dataclass(slots=True)
class MattingResult:
    foreground_dir: Path
    alpha_dir: Path
    metadata: VideoMetadata
    frame_count: int


class MattingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None

    def _load_model(self) -> torch.nn.Module:
        if self.model is not None:
            return self.model

        checkpoint_path = self.settings.rvm_checkpoint
        if not checkpoint_path.exists():
            raise FileNotFoundError(
                f"RVM checkpoint not found: {checkpoint_path}. "
                "Please download the weight file and place it in the models directory."
            )

        logger.info("loading RVM model from %s on %s", checkpoint_path, self.device)
        model = torch.hub.load(
            "PeterL1n/RobustVideoMatting",
            self.settings.rvm_variant,
            pretrained=False,
            trust_repo=True,
        )
        state_dict = torch.load(checkpoint_path, map_location=self.device)
        if isinstance(state_dict, dict) and "model_state_dict" in state_dict:
            state_dict = state_dict["model_state_dict"]
        model.load_state_dict(state_dict, strict=False)
        model = model.eval().to(self.device)
        self.model = model
        return model

    @torch.inference_mode()
    def process_video(self, source_video: Path, task_workspace: Path) -> MattingResult:
        metadata = get_video_metadata(source_video)
        model = self._load_model()
        foreground_dir = task_workspace / "foreground_frames"
        alpha_dir = task_workspace / "alpha_frames"
        foreground_dir.mkdir(parents=True, exist_ok=True)
        alpha_dir.mkdir(parents=True, exist_ok=True)

        capture = cv2.VideoCapture(str(source_video))
        if not capture.isOpened():
            raise ValueError(f"failed to open video for matting: {source_video}")

        rec = [None] * 4
        downsample_ratio = self._select_downsample_ratio(metadata.width, metadata.height)
        frame_index = 0

        while True:
            ok, frame_bgr = capture.read()
            if not ok:
                break

            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            tensor = torch.from_numpy(frame_rgb).float().div(255.0).permute(2, 0, 1).unsqueeze(0).to(self.device)
            fgr, pha, *rec = model(tensor, *rec, downsample_ratio)

            foreground = self._tensor_to_bgr(fgr[0])
            alpha = self._tensor_to_mask(pha[0])

            foreground_path = foreground_dir / f"{frame_index:06d}.png"
            alpha_path = alpha_dir / f"{frame_index:06d}.png"
            self._imwrite(foreground_path, foreground)
            self._imwrite(alpha_path, alpha)
            frame_index += 1

        capture.release()
        logger.info("matting completed, generated %s frames", frame_index)
        return MattingResult(
            foreground_dir=foreground_dir,
            alpha_dir=alpha_dir,
            metadata=metadata,
            frame_count=frame_index,
        )

    @staticmethod
    def _select_downsample_ratio(width: int, height: int) -> float:
        max_side = max(width, height)
        if max_side >= 1920:
            return 0.25
        if max_side >= 1280:
            return 0.33
        return 0.5

    @staticmethod
    def _tensor_to_bgr(tensor: torch.Tensor) -> np.ndarray:
        image = tensor.detach().clamp(0.0, 1.0).mul(255).byte().cpu().permute(1, 2, 0).numpy()
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    @staticmethod
    def _tensor_to_mask(tensor: torch.Tensor) -> np.ndarray:
        return tensor.detach().clamp(0.0, 1.0).mul(255).byte().cpu().squeeze(0).numpy()

    @staticmethod
    def _imwrite(path: Path, image: np.ndarray) -> None:
        suffix = path.suffix or ".png"
        ok, encoded = cv2.imencode(suffix, image)
        if not ok:
            raise ValueError(f"failed to encode image for write: {path}")
        encoded.tofile(str(path))
