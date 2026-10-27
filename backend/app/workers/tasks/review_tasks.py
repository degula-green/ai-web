from __future__ import annotations

from app.workers.celery_app import celery_app


@celery_app.task(name="review.run")
def run_review(task_id: str) -> dict:
    return {"task_id": task_id, "stage": "review", "status": "stub"}
