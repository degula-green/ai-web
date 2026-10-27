from __future__ import annotations

import logging
from logging.config import dictConfig

from app.core.config import LoggingSettings


def configure_logging(settings: LoggingSettings) -> None:
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    if settings.json:
        fmt = '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}'
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"default": {"format": fmt}},
            "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default"}},
            "root": {"handlers": ["console"], "level": settings.level.upper()},
        }
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
