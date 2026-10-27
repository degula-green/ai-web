from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import MediaCrawlerSettings
from app.core.logging import get_logger

from .models import MediaCrawlerJobSpec, MediaCrawlerRunResult

logger = get_logger(__name__)

SUMMARY_PATTERN = re.compile(r"---CRAWL_SUMMARY:\s*(\{.*?\})---", re.DOTALL)


class MediaCrawlerRunner:
    def __init__(self, *, settings: MediaCrawlerSettings, backend_root: Path) -> None:
        self.settings = settings
        self.backend_root = backend_root
        self.runtime_root = backend_root / "runtime" / "mediacrawler"
        self.jobs_root = self.runtime_root / "jobs"
        self.logs_root = self.runtime_root / "logs"
        self.jobs_root.mkdir(parents=True, exist_ok=True)
        self.logs_root.mkdir(parents=True, exist_ok=True)
        self.entry_script = backend_root / "app" / "crawler" / "mediacrawler" / "runner_entry.py"

    def run(self, job_spec: MediaCrawlerJobSpec) -> MediaCrawlerRunResult:
        python_dir = Path(self.settings.python_project_dir)
        if not python_dir.exists():
            raise RuntimeError(f"MediaCrawler Python project directory not found: {python_dir}")

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        spec_path = self.jobs_root / f"{job_spec.task_id}_{timestamp}.json"
        log_path = self.logs_root / f"{job_spec.task_id}_{timestamp}.log"
        spec_path.write_text(json.dumps(job_spec.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

        command = [
            self.settings.uv_bin,
            "run",
            "--directory",
            str(python_dir),
            "python",
            str(self.entry_script),
            "--job-spec",
            str(spec_path),
            "--mc-root",
            str(python_dir),
        ]

        env = os.environ.copy()
        env.update({k: str(v) for k, v in job_spec.env_overrides.items() if v is not None})
        env["PYTHONIOENCODING"] = "utf-8"
        logger.info("Launching MediaCrawler task_id=%s command=%s", job_spec.task_id, command)

        try:
            completed = subprocess.run(
                command,
                cwd=str(self.backend_root),
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=job_spec.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            output = (exc.stdout or "") + ("\n" + exc.stderr if exc.stderr else "")
            log_path.write_text(output, encoding="utf-8")
            raise RuntimeError(
                f"MediaCrawler task timed out after {job_spec.timeout_seconds}s, task_id={job_spec.task_id}"
            ) from exc

        output = (completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")
        log_path.write_text(output, encoding="utf-8")
        summary = self._parse_summary(output)
        output_tail = self._tail(output, 30)

        if completed.returncode != 0:
            raise RuntimeError(
                f"MediaCrawler exited with code {completed.returncode}, task_id={job_spec.task_id}, tail:\n{output_tail}"
            )

        return MediaCrawlerRunResult(
            task_id=job_spec.task_id,
            command=command,
            return_code=completed.returncode,
            summary=summary,
            log_path=log_path,
            output_tail=output_tail,
        )

    @staticmethod
    def _parse_summary(output: str) -> dict[str, Any]:
        match = None
        for current in SUMMARY_PATTERN.finditer(output):
            match = current
        if not match:
            return {"status": "completed", "raw": "summary_not_found"}
        raw_json = match.group(1)
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError:
            return {"status": "completed", "raw": raw_json}

    @staticmethod
    def _tail(output: str, lines: int) -> str:
        split_lines = output.splitlines()
        return "\n".join(split_lines[-lines:])
