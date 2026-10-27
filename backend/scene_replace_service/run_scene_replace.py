from __future__ import annotations

import argparse
from pathlib import Path

from app.services.compose_service import ComposeService
from app.services.file_service import FileService
from app.services.matting_service import MattingService


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local scene replacement")
    parser.add_argument("--source-video", required=True)
    parser.add_argument("--output-video", required=True)
    parser.add_argument("--output-width", type=int, default=1080)
    parser.add_argument("--output-height", type=int, default=1920)
    parser.add_argument("--background-image", default="")
    parser.add_argument("--background-video", default="")
    parser.add_argument("--task-id", default="")
    args = parser.parse_args()

    source_video = Path(args.source_video).resolve()
    output_video = Path(args.output_video).resolve()
    background_image = Path(args.background_image).resolve() if args.background_image else None
    background_video = Path(args.background_video).resolve() if args.background_video else None
    task_id = args.task_id or output_video.stem

    file_service = FileService()
    workspace = file_service.create_task_workspace(task_id)
    matting_service = MattingService()
    compose_service = ComposeService()

    matting_result = matting_service.process_video(source_video, workspace["matting"])
    compose_service.compose(
        matting_result=matting_result,
        background_image=background_image,
        background_video=background_video,
        source_video=source_video,
        output_video=output_video,
        output_width=args.output_width,
        output_height=args.output_height,
    )
    print(output_video)


if __name__ == "__main__":
    main()
