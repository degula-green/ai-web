from __future__ import annotations

from typing import Any
from sqlalchemy import select, update as sa_update
from sqlalchemy.orm import Session, sessionmaker
from contextlib import contextmanager

from app.db.models.task import TaskModel
from app.core.task_state_machine import TaskState


class TaskRecord:
    # We keep this as a DTO for compatibility with the service layer
    def __init__(
        self,
        task_id: str,
        user_id: int,
        task_type: str,
        platform: str,
        source_type: str,
        source_value: str | None,
        title: str | None,
        state: TaskState,
        config: dict[str, Any] = None,
        created_at: str = "",
        updated_at: str = "",
        error_message: str | None = None,
        result_count: int = 0
    ) -> None:
        self.task_id = task_id
        self.user_id = user_id
        self.task_type = task_type
        self.platform = platform
        self.source_type = source_type
        self.source_value = source_value
        self.title = title
        self.state = state
        self.config = config or {}
        self.created_at = created_at
        self.updated_at = updated_at
        self.error_message = error_message
        self.result_count = result_count

    @classmethod
    def from_model(cls, model: TaskModel) -> TaskRecord:
        return cls(
            task_id=model.id,
            user_id=model.user_id,
            task_type=model.task_type,
            platform=model.platform,
            source_type=model.source_type,
            source_value=model.source_value,
            title=model.title,
            state=TaskState(model.state),
            config=model.config,
            created_at=model.created_at.isoformat() if model.created_at else "",
            updated_at=model.updated_at.isoformat() if model.updated_at else "",
            error_message=model.error_message,
            result_count=model.result_count
        )


class TaskRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    @contextmanager
    def session_scope(self):
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create(self, record: TaskRecord) -> TaskRecord:
        with self.session_scope() as session:
            model = TaskModel(
                id=record.task_id,
                user_id=record.user_id,
                task_type=record.task_type,
                platform=record.platform,
                state=record.state.value if hasattr(record.state, 'value') else str(record.state),
                source_type=record.source_type,
                source_value=record.source_value,
                title=record.title,
                config=record.config,
                error_message=record.error_message,
                result_count=record.result_count
            )
            session.add(model)
            session.flush()
            return TaskRecord.from_model(model)

    def get(self, task_id: str) -> TaskRecord | None:
        with self.session_scope() as session:
            model = session.get(TaskModel, task_id)
            if model:
                return TaskRecord.from_model(model)
            return None

    def update(self, record: TaskRecord) -> TaskRecord:
        with self.session_scope() as session:
            model = session.get(TaskModel, record.task_id)
            if model:
                model.state = record.state.value if hasattr(record.state, 'value') else str(record.state)
                model.config = record.config
                model.error_message = record.error_message
                model.result_count = record.result_count
                model.title = record.title
                session.flush()
                return TaskRecord.from_model(model)
            raise ValueError(f"Task {record.task_id} not found")

    def list_by_user(self, user_id: int, limit: int = 20) -> list[TaskRecord]:
        with self.session_scope() as session:
            stmt = select(TaskModel).where(TaskModel.user_id == user_id).order_by(TaskModel.created_at.desc()).limit(limit)
            models = session.scalars(stmt).all()
            return [TaskRecord.from_model(m) for m in models]
