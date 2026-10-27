from app.core.task_state_machine import TaskState, can_transition, ensure_transition


def test_happy_path_state_transitions_are_allowed() -> None:
    assert can_transition(TaskState.CREATED, TaskState.COLLECTING)
    assert can_transition(TaskState.PARSING, TaskState.GENERATING)
    assert can_transition(TaskState.PUBLISHED, TaskState.TRACKING)


def test_invalid_transition_raises() -> None:
    try:
        ensure_transition(TaskState.CREATED, TaskState.PUBLISHED)
    except Exception as exc:  # noqa: BLE001
        assert "cannot transition" in str(exc)
    else:
        raise AssertionError("Expected invalid transition to raise")
