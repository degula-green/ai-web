from __future__ import annotations

from app.workers.celery_app import celery_app


@celery_app.task(name="parsing.run")
def run_parsing(task_id: str) -> dict:
    return {"task_id": task_id, "stage": "parsing", "status": "stub"}
