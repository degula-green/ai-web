from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Callable

from app.core.config import CelerySettings, get_settings

try:
    from celery import Celery  # type: ignore
except ImportError:
    class Celery:  # type: ignore[override]
        def __init__(self, name: str, broker: str | None = None, backend: str | None = None) -> None:
            self.name = name
            self.broker = broker
            self.backend = backend
            self.conf = SimpleNamespace(update=lambda **_: None)

        def task(self, *args: Any, **kwargs: Any) -> Callable:
            del args, kwargs

            def decorator(func: Callable) -> Callable:
                return func

            return decorator


def create_celery_app(settings: CelerySettings | None = None) -> Celery:
    resolved = settings or get_settings().celery
    app = Celery("ai_content_automation", broker=resolved.broker_url, backend=resolved.result_backend)
    app.conf.update(task_always_eager=resolved.task_always_eager, task_serializer="json", result_serializer="json")
    return app


celery_app = create_celery_app()
