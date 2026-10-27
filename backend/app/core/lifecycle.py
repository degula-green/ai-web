from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI

from app.adapters.channel.feishu_adapter import FeishuChannelPlugin
from app.adapters.llm.openai_compatible import OpenAICompatibleLLMProvider
from app.adapters.vectorstore.qdrant_adapter import QdrantVectorStoreAdapter
from app.adapters.storage.base import BaseObjectStorage
from app.adapters.storage.minio_adapter import MinIOStorageAdapter
from redis import Redis
from app.ai.context.builder import ContextBuilder
from app.ai.routing.model_router import ModelRouter
from app.crawler.mediacrawler import MediaCrawlerIntegrationService, MediaCrawlerTaskOrchestrator
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.db.repositories.iam_repository import IAMRepository
from app.db.repositories.ai_model_repository import AIModelRepository
from app.db.repositories.background_asset_repository import BackgroundAssetRepository
from app.db.repositories.video_edit_template_repository import VideoEditTemplateRepository
from app.db.repositories.avatar_draft_repository import AvatarDraftRepository
from app.db.repositories.avatar_clip_draft_repository import AvatarClipDraftRepository
from app.db.repositories.avatar_model_draft_repository import AvatarModelDraftRepository
from app.db.repositories.avatar_product_draft_repository import AvatarProductDraftRepository
from app.db.repositories.avatar_sales_draft_repository import AvatarSalesDraftRepository
from app.db.repositories.creation_draft_repository import CreationDraftRepository
from app.db.repositories.publish_plan_repository import PublishPlanRepository
from app.db.repositories.platform_account_content_repository import PlatformAccountContentRepository
from app.db.repositories.knowledge_repository import KnowledgeRepository
from app.db.repositories.material_repository import MaterialRepository
from app.db.repositories.data_collection_repository import DataCollectionRepository
from app.db.repositories.brand_knowledge_repository import BrandKnowledgeRepository
from app.db.repositories.review_repository import ReviewRepository
from app.db.repositories.task_repository import TaskRepository
from app.db.repositories.content_repository import ContentRepository
from app.db.session import build_session_factory
from app.services.auth_service import AuthService
from app.services.data_collection_service import DataCollectionService
from app.services.distribution_service import DistributionService
from app.services.douyin_crawler_service import DouyinCrawlerService
from app.services.douyin_import_service import DouyinImportService
from app.services.feedback_service import FeedbackService
from app.services.generation_service import GenerationService
from app.services.iam_service import IAMService
from app.services.knowledge_service import KnowledgeService
from app.services.brand_knowledge_service import BrandKnowledgeService
from app.services.material_service import MaterialService
from app.services.memory_service import MemoryService
from app.services.parse_service import ParseService
from app.services.platform_account_service import PlatformAccountService
from app.services.review_service import ReviewService
from app.services.task_service import TaskService
from app.services.verification_service import VerificationService
from app.services.workflow_service import WorkflowService
from app.services.ai_model_service import AIModelService
from app.services.background_asset_service import BackgroundAssetService
from app.services.video_edit_template_service import VideoEditTemplateService
from app.services.avatar_draft_service import AvatarDraftService
from app.services.avatar_clip_draft_service import AvatarClipDraftService
from app.services.avatar_model_draft_service import AvatarModelDraftService
from app.services.avatar_product_draft_service import AvatarProductDraftService
from app.services.avatar_sales_draft_service import AvatarSalesDraftService
from app.services.clip_render_service import ClipRenderService
from app.services.creation_draft_service import CreationDraftService
from app.services.publish_plan_service import PublishPlanService
from app.services.upload_service import UploadService
from app.modules.publishing.infrastructure.runtime.social_auto_upload_runtime import SocialAutoUploadRuntime

logger = get_logger(__name__)


@dataclass(slots=True)
class ServiceContainer:
    settings: Settings
    storage_adapter: BaseObjectStorage
    auth_service: AuthService
    iam_service: IAMService
    data_collection_service: DataCollectionService
    verification_service: VerificationService
    task_repository: TaskRepository
    task_service: TaskService
    material_service: MaterialService
    parse_service: ParseService
    generation_service: GenerationService
    review_service: ReviewService
    distribution_service: DistributionService
    feedback_service: FeedbackService
    workflow_service: WorkflowService
    knowledge_service: KnowledgeService
    memory_service: MemoryService
    platform_account_service: PlatformAccountService
    brand_knowledge_service: BrandKnowledgeService
    ai_model_service: AIModelService
    background_asset_service: BackgroundAssetService
    video_edit_template_service: VideoEditTemplateService
    avatar_draft_service: AvatarDraftService
    avatar_clip_draft_service: AvatarClipDraftService
    avatar_model_draft_service: AvatarModelDraftService
    avatar_product_draft_service: AvatarProductDraftService
    avatar_sales_draft_service: AvatarSalesDraftService
    creation_draft_service: CreationDraftService
    publish_plan_service: PublishPlanService
    clip_render_service: ClipRenderService
    avatar_product_clip_render_service: ClipRenderService
    avatar_sales_clip_render_service: ClipRenderService
    upload_service: UploadService
    publishing_runtime: SocialAutoUploadRuntime
    media_crawler_service: MediaCrawlerIntegrationService
    media_crawler_orchestrator: MediaCrawlerTaskOrchestrator


def build_container(settings: Settings | None = None) -> ServiceContainer:
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.logging)

    session_factory = build_session_factory(resolved_settings)
    storage_adapter = MinIOStorageAdapter(resolved_settings.storage)
    iam_repository = IAMRepository(session_factory)
    ai_model_repository = AIModelRepository(session_factory)
    verification_service = VerificationService(settings=resolved_settings, session_factory=session_factory)
    auth_service = AuthService(repository=iam_repository, verification_service=verification_service, settings=resolved_settings.auth, storage_settings=resolved_settings.storage)
    auth_service.initialize()
    iam_service = IAMService(repository=iam_repository)
    data_collection_repository = DataCollectionRepository(session_factory)
    douyin_crawler_service = DouyinCrawlerService()
    douyin_import_service = DouyinImportService()
    task_repository = TaskRepository(session_factory)
    redis_client = Redis.from_url(
        resolved_settings.redis.url,
        decode_responses=True,
        socket_timeout=5.0,
        socket_connect_timeout=5.0,
        retry_on_timeout=True,
        health_check_interval=30,
        socket_keepalive=True,
    )
    redis_binary_client = Redis.from_url(
        resolved_settings.redis.url,
        decode_responses=False,
        socket_timeout=5.0,
        socket_connect_timeout=5.0,
        retry_on_timeout=True,
        health_check_interval=30,
        socket_keepalive=True,
    )
    content_repository = ContentRepository(
        session_factory(),
        redis_client=redis_client,
        redis_binary_client=redis_binary_client,
        task_repository=task_repository,
    )
    data_collection_service = DataCollectionService(
        repository=data_collection_repository,
        content_repository=content_repository,
        crawler_service=douyin_crawler_service,
        redis_settings=resolved_settings.redis,
    )
    brand_knowledge_repository = BrandKnowledgeRepository(session_factory)
    brand_knowledge_service = BrandKnowledgeService(repository=brand_knowledge_repository, storage_adapter=storage_adapter)
    ai_model_service = AIModelService(repository=ai_model_repository)
    background_asset_repository = BackgroundAssetRepository(session_factory)
    background_asset_service = BackgroundAssetService(repository=background_asset_repository)
    background_asset_service.initialize()
    video_edit_template_repository = VideoEditTemplateRepository(session_factory)
    video_edit_template_service = VideoEditTemplateService(repository=video_edit_template_repository)
    video_edit_template_service.initialize()
    avatar_draft_repository = AvatarDraftRepository(session_factory)
    avatar_draft_service = AvatarDraftService(repository=avatar_draft_repository)
    avatar_draft_service.initialize()
    avatar_clip_draft_repository = AvatarClipDraftRepository(session_factory)
    avatar_model_draft_repository = AvatarModelDraftRepository(session_factory)
    avatar_product_draft_repository = AvatarProductDraftRepository(session_factory)
    avatar_sales_draft_repository = AvatarSalesDraftRepository(session_factory)
    creation_draft_repository = CreationDraftRepository(session_factory)
    creation_draft_repository.ensure_table()
    avatar_clip_draft_service = AvatarClipDraftService(
        repository=avatar_clip_draft_repository,
        avatar_repository=avatar_draft_repository,
        creation_repository=creation_draft_repository,
    )
    avatar_clip_draft_service.initialize()
    avatar_model_draft_service = AvatarModelDraftService(
        repository=avatar_model_draft_repository,
        avatar_repository=avatar_draft_repository,
        creation_repository=creation_draft_repository,
    )
    avatar_model_draft_service.initialize()
    avatar_product_draft_service = AvatarProductDraftService(
        repository=avatar_product_draft_repository,
        avatar_repository=avatar_draft_repository,
        creation_repository=creation_draft_repository,
    )
    avatar_product_draft_service.initialize()
    avatar_sales_draft_service = AvatarSalesDraftService(
        repository=avatar_sales_draft_repository,
        avatar_repository=avatar_draft_repository,
        creation_repository=creation_draft_repository,
    )
    avatar_sales_draft_service.initialize()
    creation_draft_service = CreationDraftService(repository=creation_draft_repository, avatar_repository=avatar_draft_repository)
    creation_draft_service.initialize()
    backend_root = Path(__file__).resolve().parents[2]
    publish_plan_repository = PublishPlanRepository(session_factory)
    publish_plan_service = PublishPlanService(repository=publish_plan_repository)
    publish_plan_service.initialize()
    platform_account_content_repository = PlatformAccountContentRepository(session_factory)
    platform_account_content_repository.ensure_table()
    clip_render_service = ClipRenderService(
        repository=creation_draft_repository,
        storage=storage_adapter,
        backend_root=backend_root,
    )
    avatar_product_clip_render_service = ClipRenderService(
        repository=avatar_product_draft_repository,
        storage=storage_adapter,
        backend_root=backend_root,
    )
    avatar_sales_clip_render_service = ClipRenderService(
        repository=avatar_sales_draft_repository,
        storage=storage_adapter,
        backend_root=backend_root,
    )
    upload_service = UploadService(storage=storage_adapter)
    publishing_runtime = SocialAutoUploadRuntime(backend_root=backend_root)

    material_repository = MaterialRepository()
    review_repository = ReviewRepository()
    knowledge_repository = KnowledgeRepository()

    llm_provider = OpenAICompatibleLLMProvider(resolved_settings.llm)
    vector_store = QdrantVectorStoreAdapter(resolved_settings.qdrant)
    model_router = ModelRouter(resolved_settings.llm)
    context_builder = ContextBuilder()
    channel_plugin = FeishuChannelPlugin(resolved_settings.feishu)

    memory_service = MemoryService()
    knowledge_service = KnowledgeService(knowledge_repository=knowledge_repository, vector_store=vector_store)
    parse_service = ParseService(llm_provider=llm_provider, model_router=model_router, context_builder=context_builder)
    generation_service = GenerationService(
        llm_provider=llm_provider,
        model_router=model_router,
        context_builder=context_builder,
        knowledge_service=knowledge_service,
    )
    review_service = ReviewService(llm_provider=llm_provider, model_router=model_router, review_repository=review_repository)
    distribution_service = DistributionService(
        channel_plugin=channel_plugin,
        session_factory=session_factory,
        content_repository=content_repository,
        platform_account_content_repository=platform_account_content_repository,
        creation_draft_repository=creation_draft_repository,
        publish_plan_repository=publish_plan_repository,
        publisher_runtime=publishing_runtime,
    )
    feedback_service = FeedbackService()
    workflow_service = WorkflowService()
    material_service = MaterialService(material_repository=material_repository)
    media_crawler_service = MediaCrawlerIntegrationService(
        settings=resolved_settings.media_crawler,
        mysql_settings=resolved_settings.mysql,
        redis_settings=resolved_settings.redis,
        logging_settings=resolved_settings.logging,
        backend_root=Path(__file__).resolve().parents[2],
    )
    media_crawler_orchestrator = MediaCrawlerTaskOrchestrator(
        task_repository=task_repository,
        memory_service=memory_service,
        crawler_service=media_crawler_service,
        redis_settings=resolved_settings.redis,
        enabled=resolved_settings.media_crawler.enabled,
    )
    task_service = TaskService(
        task_repository=task_repository,
        memory_service=memory_service,
        task_start_executor=media_crawler_orchestrator,
    )
    from app.services.platform_account_service import platform_account_service

    logger.info("Service container initialized with task_store_backend=%s", resolved_settings.app.task_store_backend)

    return ServiceContainer(
        settings=resolved_settings,
        storage_adapter=storage_adapter,
        auth_service=auth_service,
        iam_service=iam_service,
        data_collection_service=data_collection_service,
        verification_service=verification_service,
        task_repository=task_repository,
        task_service=task_service,
        material_service=material_service,
        parse_service=parse_service,
        generation_service=generation_service,
        review_service=review_service,
        distribution_service=distribution_service,
        feedback_service=feedback_service,
        workflow_service=workflow_service,
        knowledge_service=knowledge_service,
        memory_service=memory_service,
        platform_account_service=platform_account_service,
        brand_knowledge_service=brand_knowledge_service,
        ai_model_service=ai_model_service,
        background_asset_service=background_asset_service,
        video_edit_template_service=video_edit_template_service,
        avatar_draft_service=avatar_draft_service,
        avatar_clip_draft_service=avatar_clip_draft_service,
        avatar_model_draft_service=avatar_model_draft_service,
        avatar_product_draft_service=avatar_product_draft_service,
        avatar_sales_draft_service=avatar_sales_draft_service,
        creation_draft_service=creation_draft_service,
        publish_plan_service=publish_plan_service,
        clip_render_service=clip_render_service,
        avatar_product_clip_render_service=avatar_product_clip_render_service,
        avatar_sales_clip_render_service=avatar_sales_clip_render_service,
        upload_service=upload_service,
        publishing_runtime=publishing_runtime,
        media_crawler_service=media_crawler_service,
        media_crawler_orchestrator=media_crawler_orchestrator,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = build_container()
    app.state.container = container
    # 彻底解耦：不再由后端管理爬虫子进程的生命周期
    # await container.media_crawler_service.startup() 
    try:
        yield
    finally:
        # await container.media_crawler_service.shutdown()
        pass
