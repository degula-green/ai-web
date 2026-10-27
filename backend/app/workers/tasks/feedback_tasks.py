from __future__ import annotations

from app.workers.celery_app import celery_app


@celery_app.task(name="feedback.run")
def run_feedback_sync(task_id: str) -> dict:
    return {"task_id": task_id, "stage": "feedback", "status": "stub"}
