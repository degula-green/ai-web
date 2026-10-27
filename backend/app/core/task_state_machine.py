from __future__ import annotations

from enum import StrEnum

from app.core.exceptions import StateTransitionError


class TaskState(StrEnum):
    CREATED = "created"
    COLLECTING = "collecting"
    PARSING = "parsing"
    GENERATING = "generating"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    TRACKING = "tracking"
    CLOSED = "closed"
    FAILED = "failed"
    RETRYING = "retrying"
    MANUAL_INTERVENTION = "manual_intervention"


ALLOWED_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.CREATED: {TaskState.COLLECTING, TaskState.FAILED, TaskState.MANUAL_INTERVENTION},
    TaskState.COLLECTING: {TaskState.PARSING, TaskState.FAILED, TaskState.RETRYING, TaskState.MANUAL_INTERVENTION},
    TaskState.PARSING: {TaskState.GENERATING, TaskState.FAILED, TaskState.RETRYING, TaskState.MANUAL_INTERVENTION},
    TaskState.GENERATING: {TaskState.REVIEWING, TaskState.FAILED, TaskState.RETRYING, TaskState.MANUAL_INTERVENTION},
    TaskState.REVIEWING: {TaskState.APPROVED, TaskState.FAILED, TaskState.RETRYING, TaskState.MANUAL_INTERVENTION},
    TaskState.APPROVED: {TaskState.PUBLISHING, TaskState.CLOSED, TaskState.MANUAL_INTERVENTION},
    TaskState.PUBLISHING: {TaskState.PUBLISHED, TaskState.FAILED, TaskState.RETRYING, TaskState.MANUAL_INTERVENTION},
    TaskState.PUBLISHED: {TaskState.TRACKING, TaskState.CLOSED, TaskState.MANUAL_INTERVENTION},
    TaskState.TRACKING: {TaskState.CLOSED, TaskState.MANUAL_INTERVENTION},
    TaskState.CLOSED: set(),
    TaskState.FAILED: {TaskState.RETRYING, TaskState.MANUAL_INTERVENTION, TaskState.CLOSED},
    TaskState.RETRYING: {
        TaskState.COLLECTING,
        TaskState.PARSING,
        TaskState.GENERATING,
        TaskState.REVIEWING,
        TaskState.PUBLISHING,
        TaskState.TRACKING,
        TaskState.FAILED,
        TaskState.MANUAL_INTERVENTION,
    },
    TaskState.MANUAL_INTERVENTION: {
        TaskState.COLLECTING,
        TaskState.PARSING,
        TaskState.GENERATING,
        TaskState.REVIEWING,
        TaskState.APPROVED,
        TaskState.PUBLISHING,
        TaskState.TRACKING,
        TaskState.CLOSED,
        TaskState.FAILED,
    },
}


def can_transition(current: TaskState, target: TaskState) -> bool:
    if current == target:
        return True
    return target in ALLOWED_TRANSITIONS.get(current, set())


def ensure_transition(current: TaskState, target: TaskState) -> None:
    if not can_transition(current, target):
        raise StateTransitionError(f"Task state cannot transition from {current} to {target}")


def next_states(current: TaskState) -> list[TaskState]:
    return sorted(ALLOWED_TRANSITIONS.get(current, set()), key=lambda value: value.value)
