from __future__ import annotations

from app.workers.celery_app import celery_app


@celery_app.task(name="generation.run")
def run_generation(task_id: str) -> dict:
    return {"task_id": task_id, "stage": "generation", "status": "stub"}
