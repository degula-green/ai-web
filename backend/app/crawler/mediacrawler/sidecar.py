from __future__ import annotations

import asyncio
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from app.core.config import LoggingSettings, MediaCrawlerSettings
from app.core.exceptions import ConfigurationError
from app.core.logging import get_logger
import sys
from urllib.parse import urlparse

logger = get_logger(__name__)


class SignSrvSidecar:
    def __init__(self, *, settings: MediaCrawlerSettings, logging_settings: LoggingSettings) -> None:
        self.settings = settings
        self.logging_settings = logging_settings
        self._process: asyncio.subprocess.Process | None = None
        self._managed = False
        self._last_error: str | None = None
        self._started_at: datetime | None = None
        self._stdout_log = None
        self._stderr_log = None

    @property
    def endpoint(self) -> str:
        return f"http://{self.settings.signsrv_host}:{self.settings.signsrv_port}"

    async def ensure_started(self) -> None:
        if not self.settings.enabled or not self.settings.signsrv_autostart:
            return

        signsrv_dir = Path(self.settings.signsrv_project_dir)
        if not signsrv_dir.exists():
            self._last_error = f"SignSrv project directory not found: {signsrv_dir}"
            if self.settings.signsrv_strict_startup:
                raise ConfigurationError(self._last_error)
            logger.warning(self._last_error)
            return

        if await self.is_healthy():
            logger.info("MediaCrawler SignSrv already healthy at %s", self.endpoint)
            self._managed = False
            self._last_error = None
            return

        cmd = [
            sys.executable,
            "app.py",
        ]
        env = os.environ.copy()
        env.pop("VIRTUAL_ENV", None)
        env.pop("PYTHONPATH", None)
        env.update(
            {
                "APP_PORT": str(self.settings.signsrv_port),
                "APP_ADDRESS": self.settings.signsrv_bind_address,
                "SIGN_TYPE": self.settings.signsrv_sign_type,
                "playwright_headless": "true" if self.settings.signsrv_playwright_headless else "false",
                "LOGGER_LEVEL": self.logging_settings.level,
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUNBUFFERED": "1",
            }
        )

        try:
            log_dir = Path(self.settings.python_project_dir).parent.parent / "runtime" / "mediacrawler" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            self._stdout_log = open(log_dir / "signsrv_stdout.log", "a", encoding="utf-8")
            self._stderr_log = open(log_dir / "signsrv_stderr.log", "a", encoding="utf-8")

            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.settings.signsrv_project_dir,
                env=env,
                stdout=self._stdout_log,
                stderr=self._stderr_log,
            )
        except FileNotFoundError as exc:
            self._last_error = f"Failed to start SignSrv: {exc}"
            raise ConfigurationError(self._last_error) from exc

        self._managed = True
        self._started_at = datetime.now(timezone.utc)
        self._last_error = None
        logger.info("MediaCrawler SignSrv started, pid=%s", self._process.pid)

        deadline = asyncio.get_running_loop().time() + self.settings.signsrv_startup_timeout_seconds
        while asyncio.get_running_loop().time() < deadline:
            if self._process.returncode is not None:
                self._last_error = f"SignSrv exited unexpectedly with code {self._process.returncode}"
                break
            if await self.is_healthy():
                logger.info("MediaCrawler SignSrv is healthy at %s", self.endpoint)
                return
            await asyncio.sleep(0.5)

        await self.shutdown()
        if self._last_error is None:
            self._last_error = "SignSrv startup timeout"
        if self.settings.signsrv_strict_startup:
            raise ConfigurationError(self._last_error)
        logger.warning("MediaCrawler SignSrv startup degraded: %s", self._last_error)

    async def is_healthy(self) -> bool:
        url = f"{self.endpoint}/signsrv/pong"
        try:
            async with httpx.AsyncClient(timeout=2.0, trust_env=False) as client:
                resp = await client.get(url)
            return resp.status_code == 200
        except Exception:
            return False

    async def shutdown(self) -> None:
        process = self._process
        self._process = None
        if not process:
            return
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=10)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
        if hasattr(self, "_stdout_log") and self._stdout_log:
            self._stdout_log.close()
        if hasattr(self, "_stderr_log") and self._stderr_log:
            self._stderr_log.close()
        logger.info("MediaCrawler SignSrv stopped, return_code=%s", process.returncode)

    def status(self) -> dict[str, Any]:
        process = self._process
        return {
            "enabled": self.settings.enabled,
            "endpoint": self.endpoint,
            "autostart": self.settings.signsrv_autostart,
            "managed": self._managed,
            "pid": process.pid if process else None,
            "running": bool(process and process.returncode is None),
            "last_error": self._last_error,
            "started_at": self._started_at.isoformat() if self._started_at else None,
        }


class CrawlerEngineSidecar:
    def __init__(self, *, settings: MediaCrawlerSettings, backend_root: Path) -> None:
        self.settings = settings
        self.backend_root = backend_root
        self._process: asyncio.subprocess.Process | None = None
        self._last_error: str | None = None
        self._started_at: datetime | None = None
        self._stdout_log = None
        self._stderr_log = None

    @property
    def endpoint(self) -> str:
        return self.settings.crawler_api_base_url.rstrip("/")

    async def ensure_started(self) -> None:
        if not self.settings.enabled:
            return

        python_dir = Path(self.settings.python_project_dir)
        if not python_dir.exists():
            self._last_error = f"MediaCrawler Python project directory not found: {python_dir}"
            logger.warning(self._last_error)
            return

        if self._process and self._process.returncode is None:
            return

        if await self.is_healthy():
            self._last_error = None
            logger.info("MediaCrawler Engine resident API already healthy at %s", self.endpoint)
            return

        cmd = [
            sys.executable,
            "api_server.py",
        ]

        env = os.environ.copy()
        env.pop("VIRTUAL_ENV", None)
        env.pop("PYTHONPATH", None)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"
        
        # Pass database configuration to ensure worker uses the same DB as backend
        from app.core.config import get_settings
        settings = get_settings()
        env["RELATION_DB_HOST"] = settings.mysql.host
        env["RELATION_DB_PORT"] = str(settings.mysql.port)
        env["RELATION_DB_USER"] = settings.mysql.user
        env["RELATION_DB_PWD"] = settings.mysql.password
        env["RELATION_DB_NAME"] = settings.mysql.database
        env["DB_TYPE"] = "mysql"
        env["REDIS_DB_HOST"] = settings.redis.host
        env["REDIS_DB_PORT"] = str(settings.redis.port)
        env["REDIS_DB_PWD"] = settings.redis.password
        env["REDIS_DB_NUM"] = str(settings.redis.db)
        parsed_api_url = urlparse(self.endpoint)
        if parsed_api_url.port:
            env["CRAWLER_API_PORT"] = str(parsed_api_url.port)

        log_dir = self.backend_root / "runtime" / "mediacrawler" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        self._stdout_log = open(log_dir / "crawler_engine_stdout.log", "a", encoding="utf-8")
        self._stderr_log = open(log_dir / "crawler_engine_stderr.log", "a", encoding="utf-8")

        try:
            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.settings.python_project_dir,
                env=env,
                stdout=self._stdout_log,
                stderr=self._stderr_log,
            )
            self._started_at = datetime.now(timezone.utc)
            self._last_error = None
            logger.info("MediaCrawler Engine resident service started, pid=%s", self._process.pid)
        except Exception as exc:
            self._last_error = f"Failed to start MediaCrawler Engine: {exc}"
            logger.error(self._last_error)

    async def is_healthy(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0, trust_env=False) as client:
                resp = await client.get(f"{self.endpoint}/openapi.json")
            return resp.status_code == 200
        except Exception:
            return False

    async def shutdown(self) -> None:
        process = self._process
        self._process = None
        if not process:
            return
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
        if hasattr(self, "_stdout_log") and self._stdout_log:
            self._stdout_log.close()
        if hasattr(self, "_stderr_log") and self._stderr_log:
            self._stderr_log.close()
        logger.info("MediaCrawler Engine resident service stopped, return_code=%s", process.returncode)

    def status(self) -> dict[str, Any]:
        process = self._process
        return {
            "enabled": self.settings.enabled,
            "endpoint": self.endpoint,
            "pid": process.pid if process else None,
            "running": bool(process and process.returncode is None),
            "last_error": self._last_error,
            "started_at": self._started_at.isoformat() if self._started_at else None,
        }
