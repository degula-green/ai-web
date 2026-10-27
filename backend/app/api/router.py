from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.avatar_drafts import router as avatar_drafts_router
from app.api.v1.avatar_clip_drafts import router as avatar_clip_drafts_router
from app.api.v1.avatar_model_drafts import router as avatar_model_drafts_router
from app.api.v1.avatar_product_drafts import router as avatar_product_drafts_router
from app.api.v1.avatar_sales_drafts import router as avatar_sales_drafts_router
from app.api.v1.brand_knowledge import router as brand_knowledge_router
from app.api.v1.creation_drafts import router as creation_drafts_router
from app.api.v1.data_collection import router as data_collection_router
from app.api.v1.distribution import router as distribution_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.generation import router as generation_router
from app.api.v1.health import router as health_router
from app.api.v1.iam import router as iam_router
from app.api.v1.knowledge_base import router as knowledge_router
from app.api.v1.platform_account import router as platform_account_router
from app.api.v1.ai_model import router as ai_model_router
from app.api.v1.background_assets import router as background_assets_router
from app.api.v1.video_edit_templates import router as video_edit_templates_router
from app.api.v1.materials import router as materials_router
from app.api.v1.parsing import router as parsing_router
from app.api.v1.review import router as review_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.uploads import router as uploads_router
from app.api.v1.workflows import router as workflows_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(data_collection_router, prefix="/data-collection", tags=["data-collection"])
api_router.include_router(iam_router, prefix="/iam", tags=["iam"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(materials_router, prefix="/materials", tags=["materials"])
api_router.include_router(parsing_router, prefix="/parsing", tags=["parsing"])
api_router.include_router(generation_router, prefix="/generation", tags=["generation"])
api_router.include_router(review_router, prefix="/review", tags=["review"])
api_router.include_router(distribution_router, prefix="/distribution", tags=["distribution"])
api_router.include_router(feedback_router, prefix="/feedback", tags=["feedback"])
api_router.include_router(workflows_router, prefix="/workflows", tags=["workflows"])
api_router.include_router(knowledge_router, prefix="/knowledge-base", tags=["knowledge-base"])
api_router.include_router(platform_account_router, prefix="/platforms", tags=["platforms"])
api_router.include_router(brand_knowledge_router, prefix="/brand-knowledge", tags=["brand-knowledge"])
api_router.include_router(ai_model_router, prefix="/ai-models", tags=["ai-models"])
api_router.include_router(background_assets_router, prefix="/background-assets", tags=["background-assets"])
api_router.include_router(video_edit_templates_router, prefix="/video-edit-templates", tags=["video-edit-templates"])
api_router.include_router(avatar_drafts_router, prefix="/avatar-drafts", tags=["avatar-drafts"])
api_router.include_router(avatar_clip_drafts_router, prefix="/avatar-clip-drafts", tags=["avatar-clip-drafts"])
api_router.include_router(avatar_model_drafts_router, prefix="/avatar-model-drafts", tags=["avatar-model-drafts"])
api_router.include_router(avatar_product_drafts_router, prefix="/avatar-product-drafts", tags=["avatar-product-drafts"])
api_router.include_router(avatar_sales_drafts_router, prefix="/avatar-sales-drafts", tags=["avatar-sales-drafts"])
api_router.include_router(creation_drafts_router, prefix="/creation-drafts", tags=["creation-drafts"])
api_router.include_router(uploads_router, prefix="/uploads", tags=["uploads"])
