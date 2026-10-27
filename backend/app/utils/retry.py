from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from time import sleep
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def retry_sync(*, attempts: int = 3, delay_seconds: float = 0.0) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_error: Exception | None = None
            for _ in range(attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    if delay_seconds:
                        sleep(delay_seconds)
            assert last_error is not None
            raise last_error

        return wrapper

    return decorator
