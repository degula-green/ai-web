from __future__ import annotations

from app.workers.celery_app import celery_app


@celery_app.task(name="distribution.run")
def run_distribution(task_id: str) -> dict:
    return {"task_id": task_id, "stage": "distribution", "status": "stub"}
