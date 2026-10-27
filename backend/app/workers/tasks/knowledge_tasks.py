from __future__ import annotations

from app.workers.celery_app import celery_app


@celery_app.task(name="knowledge.sync")
def sync_knowledge_item(item_id: str) -> dict:
    return {"item_id": item_id, "stage": "knowledge", "status": "stub"}
