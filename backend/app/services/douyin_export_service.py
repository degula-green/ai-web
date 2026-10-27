from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


class DouyinExportService:
    def __init__(self) -> None:
        self.export_root = Path(__file__).resolve().parents[2] / "exports" / "data_collection"
        self.export_root.mkdir(parents=True, exist_ok=True)

    def export_rows(
        self,
        *,
        prefix: str,
        rows: list[dict[str, Any]],
        file_type: str,
    ) -> dict[str, Any]:
        normalized_type = file_type.lower().strip() if file_type else "csv"
        if normalized_type not in {"csv", "json"}:
            raise ValueError("fileType 仅支持 csv 或 json")

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_no = f"EX{datetime.now().strftime('%Y%m%d%H%M%S')}"
        filename = f"{prefix}_{stamp}.{normalized_type}"
        filepath = self.export_root / filename

        if normalized_type == "csv":
            self._write_csv(filepath, rows)
        else:
            self._write_json(filepath, rows)

        return {
            "exportNo": export_no,
            "fileType": normalized_type,
            "fileName": filename,
            "filePath": str(filepath.resolve()),
            "downloadUrl": str(filepath.resolve()),
            "expireAt": None,
        }

    @staticmethod
    def _write_csv(filepath: Path, rows: list[dict[str, Any]]) -> None:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        keys: list[str] = []
        for row in rows:
            for key in row.keys():
                if key not in keys:
                    keys.append(key)
        with filepath.open("w", encoding="utf-8-sig", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=keys)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: _flatten_value(row.get(key)) for key in keys})

    @staticmethod
    def _write_json(filepath: Path, rows: list[dict[str, Any]]) -> None:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(json.dumps(rows, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _flatten_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)

