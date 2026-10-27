from __future__ import annotations

import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class DouyinCrawlerService:
    def __init__(self) -> None:
        self._backend_root = Path(__file__).resolve().parents[2]
        self._runtime_root = self._backend_root / "runtime" / "data_collection"
        self._runtime_root.mkdir(parents=True, exist_ok=True)
