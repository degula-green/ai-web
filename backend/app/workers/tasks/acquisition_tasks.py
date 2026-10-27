from __future__ import annotations

from app.workers.celery_app import celery_app


@celery_app.task(name="acquisition.collect")
def collect_material(task_id: str) -> dict:
    return {"task_id": task_id, "stage": "collecting", "status": "stub"}
