from __future__ import annotations

from typing import Protocol

from app.core.exceptions import NotFoundError
from app.core.task_state_machine import TaskState, ensure_transition
from app.db.repositories.task_repository import TaskRecord, TaskRepository
from app.schemas.task import TaskCreateRequest, TaskRead
from app.services.memory_service import MemoryService
from app.utils.ids import generate_id
from app.utils.time import utc_now_iso


class TaskStartExecutor(Protocol):
    def validate_before_submit(self, record: TaskRecord) -> None:
        ...

    def submit(self, record: TaskRecord) -> bool:
        ...

    def sync_task_status(self, record: TaskRecord) -> TaskRecord:
        ...


class TaskService:
    def __init__(
        self,
        *,
        task_repository: TaskRepository,
        memory_service: MemoryService,
        task_start_executor: TaskStartExecutor | None = None,
    ) -> None:
        self.task_repository = task_repository
        self.memory_service = memory_service
        self.task_start_executor = task_start_executor

    def create_task(self, payload: TaskCreateRequest, user_id: int) -> TaskRead:
        now = utc_now_iso()
        record = TaskRecord(
            task_id=generate_id("task"),
            user_id=user_id,
            task_type=payload.task_type,
            platform=payload.platform,
            source_type=payload.source_type,
            source_value=payload.source_value,
            title=payload.title,
            state=TaskState.CREATED,
            config=payload.config,
            created_at=now,
            updated_at=now,
        )
        if payload.start_async and self.task_start_executor:
            validator = getattr(self.task_start_executor, "validate_before_submit", None)
            if callable(validator):
                validator(record)
        stored = self.task_repository.create(record)
        self.memory_service.record_event(task_id=stored.task_id, snapshot_type="task_created", summary="Task created")
        if payload.start_async and self.task_start_executor:
            submitted = self.task_start_executor.submit(stored)
            if submitted:
                stored = self.task_repository.get(stored.task_id) or stored
                self.memory_service.record_event(
                    task_id=stored.task_id,
                    snapshot_type="task_async_submitted",
                    summary="Task submitted to MediaCrawler orchestrator",
                )
        return self._to_schema(stored)

    def get_task(self, task_id: str) -> TaskRead:
        record = self.task_repository.get(task_id)
        if record is None:
            raise NotFoundError(f"Task {task_id} not found")
        if self.task_start_executor:
            record = self.task_start_executor.sync_task_status(record)
        return self._to_schema(record)

    def transition(self, task_id: str, target_state: TaskState) -> TaskRead:
        record = self.task_repository.get(task_id)
        if record is None:
            raise NotFoundError(f"Task {task_id} not found")
        previous_state = record.state
        ensure_transition(previous_state, target_state)
        record.state = target_state
        record.updated_at = utc_now_iso()
        self.task_repository.update(record)
        self.memory_service.record_event(
            task_id=task_id,
            snapshot_type="state_transition",
            summary=f"{previous_state} -> {target_state}",
        )
        return self._to_schema(record)

    @staticmethod
    def _to_schema(record: TaskRecord) -> TaskRead:
        return TaskRead(
            task_id=record.task_id,
            task_type=record.task_type,
            platform=record.platform,
            source_type=record.source_type,
            source_value=record.source_value,
            title=record.title,
            state=record.state,
            config=record.config,
            created_at=record.created_at,
            updated_at=record.updated_at,
            error_message=record.error_message,
        )
