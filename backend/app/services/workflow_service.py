from __future__ import annotations

from app.schemas.workflow import WorkflowBlueprint, WorkflowStep


class WorkflowService:
    def default_blueprint(self) -> WorkflowBlueprint:
        return WorkflowBlueprint(
            name="mvp_content_workflow",
            steps=[
                WorkflowStep(code="collecting", label="Collect Source"),
                WorkflowStep(code="parsing", label="Parse Source"),
                WorkflowStep(code="generating", label="Generate Content"),
                WorkflowStep(code="reviewing", label="Review Content"),
                WorkflowStep(code="publishing", label="Publish Content"),
                WorkflowStep(code="tracking", label="Track Metrics"),
            ],
        )
