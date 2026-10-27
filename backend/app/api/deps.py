from __future__ import annotations

from fastapi import Header, Request

from app.core.exceptions import ContractError
from app.core.lifecycle import ServiceContainer, build_container


def get_container(request: Request) -> ServiceContainer:
    if not hasattr(request.app.state, "container"):
        request.app.state.container = build_container()
    return request.app.state.container


def get_task_service(request: Request):
    return get_container(request).task_service


def get_material_service(request: Request):
    return get_container(request).material_service


def get_parse_service(request: Request):
    return get_container(request).parse_service


def get_generation_service(request: Request):
    return get_container(request).generation_service


def get_review_service(request: Request):
    return get_container(request).review_service


def get_distribution_service(request: Request):
    return get_container(request).distribution_service


def get_feedback_service(request: Request):
    return get_container(request).feedback_service


def get_workflow_service(request: Request):
    return get_container(request).workflow_service


def get_knowledge_service(request: Request):
    return get_container(request).knowledge_service


def get_auth_service(request: Request):
    return get_container(request).auth_service


def get_iam_service(request: Request):
    return get_container(request).iam_service


def get_data_collection_service(request: Request):
    return get_container(request).data_collection_service


def get_platform_account_service(request: Request):
    return get_container(request).platform_account_service


def get_brand_knowledge_service(request: Request):
    return get_container(request).brand_knowledge_service


def get_ai_model_service(request: Request):
    return get_container(request).ai_model_service


def get_creation_draft_service(request: Request):
    return get_container(request).creation_draft_service


def get_avatar_draft_service(request: Request):
    return get_container(request).avatar_draft_service


def get_avatar_model_draft_service(request: Request):
    return get_container(request).avatar_model_draft_service


def get_avatar_sales_draft_service(request: Request):
    return get_container(request).avatar_sales_draft_service


def get_avatar_product_draft_service(request: Request):
    return get_container(request).avatar_product_draft_service


def get_avatar_clip_draft_service(request: Request):
    return get_container(request).avatar_clip_draft_service


def get_upload_service(request: Request):
    return get_container(request).upload_service


def get_clip_render_service(request: Request):
    return get_container(request).clip_render_service


def get_avatar_sales_clip_render_service(request: Request):
    return get_container(request).avatar_sales_clip_render_service


def get_avatar_product_clip_render_service(request: Request):
    return get_container(request).avatar_product_clip_render_service


def get_publish_plan_service(request: Request):
    return get_container(request).publish_plan_service


def get_background_asset_service(request: Request):
    return get_container(request).background_asset_service


def get_video_edit_template_service(request: Request):
    return get_container(request).video_edit_template_service


def get_current_auth_context(request: Request, authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise ContractError("未登录或登录已失效", status_code=401)
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise ContractError("未登录或登录已失效", status_code=401)
    return get_auth_service(request).authenticate_access_token(token)
