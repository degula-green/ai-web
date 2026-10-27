"""SQLAlchemy model declarations."""

from app.db.models.iam import (
    IAMLoginLog,
    IAMOperationLog,
    IAMPermission,
    IAMRole,
    IAMRolePermission,
    IAMSession,
    IAMUser,
    IAMUserIdentity,
    IAMUserRole,
    IamLoginLogModel,
    IamOperationLogModel,
    IamPermissionModel,
    IamRoleModel,
    IamRolePermissionModel,
    IamSessionModel,
    IamUserIdentityModel,
    IamUserModel,
    IamUserRoleModel,
)
from app.db.models.douyin_data_collection import (
    DouyinHotRankItem,
)
from app.db.models.brand_knowledge import (
    BrandProduct,
    BrandSellingPoint,
    BrandVisualAsset,
)
from app.db.models.platform_account import (
    CrawlerCookieAccountBinding,
    PlatformCookieBridgeBinding,
    PlatformAccount,
    PlatformAccountAuthLog,
    PlatformAccountSession,
)
from app.db.models.ai_model import (
    AIModelProviderConfig,
    AITokenUsageLog,
)
from app.db.models.creation_draft import CreationDraftModel
from app.db.models.avatar_draft import AvatarDraftModel
from app.db.models.avatar_model_draft import AvatarModelDraftModel
from app.db.models.avatar_product_draft import AvatarProductDraftModel
from app.db.models.avatar_sales_draft import AvatarSalesDraftModel
from app.db.models.background_asset import BackgroundAssetModel
from app.db.models.video_edit_template import VideoEditTemplateModel
from app.db.models.publish_plan import PublishPlanItemModel
from app.db.models.platform_account_content import PlatformAccountContent

__all__ = [
    "IAMLoginLog",
    "IAMOperationLog",
    "IAMPermission",
    "IAMRole",
    "IAMRolePermission",
    "IAMSession",
    "IAMUser",
    "IAMUserIdentity",
    "IAMUserRole",
    "IamLoginLogModel",
    "IamOperationLogModel",
    "IamPermissionModel",
    "IamRoleModel",
    "IamRolePermissionModel",
    "IamSessionModel",
    "IamUserIdentityModel",
    "IamUserModel",
    "IamUserRoleModel",
    "DouyinHotRankItem",
    "BrandProduct",
    "BrandSellingPoint",
    "BrandVisualAsset",
    "PlatformAccount",
    "PlatformAccountSession",
    "PlatformAccountAuthLog",
    "CrawlerCookieAccountBinding",
    "PlatformCookieBridgeBinding",
    "AIModelProviderConfig",
    "AITokenUsageLog",
    "CreationDraftModel",
    "AvatarDraftModel",
    "AvatarModelDraftModel",
    "AvatarProductDraftModel",
    "AvatarSalesDraftModel",
    "BackgroundAssetModel",
    "VideoEditTemplateModel",
    "PublishPlanItemModel",
    "PlatformAccountContent",
]
