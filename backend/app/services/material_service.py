from __future__ import annotations

from app.db.repositories.material_repository import MaterialRecord, MaterialRepository
from app.schemas.material import MaterialIngestRequest, MaterialRead
from app.utils.ids import generate_id


class MaterialService:
    def __init__(self, *, material_repository: MaterialRepository) -> None:
        self.material_repository = material_repository

    def ingest(self, payload: MaterialIngestRequest) -> MaterialRead:
        record = MaterialRecord(
            material_id=generate_id("mat"),
            task_id=payload.task_id,
            material_type=payload.material_type,
            source_value=payload.source_value,
            metadata=payload.metadata,
        )
        saved = self.material_repository.create(record)
        return MaterialRead(
            material_id=saved.material_id,
            task_id=saved.task_id,
            material_type=saved.material_type,
            source_value=saved.source_value,
            metadata=saved.metadata,
        )
