from __future__ import annotations

from app.schemas.feedback import FeedbackSummary


class FeedbackService:
    def get_summary(self, task_id: str) -> FeedbackSummary:
        return FeedbackSummary(task_id=task_id, metrics={"exposure": 0.0, "engagement_rate": 0.0})
