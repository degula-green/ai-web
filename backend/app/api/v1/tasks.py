from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import get_task_service, get_current_auth_context
from app.core.contract import contract_success
from app.schemas.task import TaskCreateRequest, TaskRead, TaskTransitionRequest
from app.services.task_service import TaskService

router = APIRouter()


@router.get("/ping")
def ping_tasks() -> Any:
    return {"status": "ok", "version": "v1.2-numeric-code-enforced", "code": 200}


@router.post("")
def create_task(
    payload: TaskCreateRequest,
    service: TaskService = Depends(get_task_service),
    auth_context=Depends(get_current_auth_context),
) -> Any:
    return contract_success(service.create_task(payload, user_id=auth_context.user.id), msg="task created")


@router.get("/{task_id}")
def get_task(task_id: str, service: TaskService = Depends(get_task_service)) -> Any:
    return contract_success(service.get_task(task_id))


@router.post("/{task_id}/transition")
def transition_task(
    task_id: str,
    payload: TaskTransitionRequest,
    service: TaskService = Depends(get_task_service),
) -> Any:
    return contract_success(service.transition(task_id, payload.target_state), msg="task transitioned")
