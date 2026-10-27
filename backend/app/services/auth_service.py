from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.core.config import AuthSettings, StorageSettings
from app.core.exceptions import ContractError
from app.core.logging import get_logger
from app.core.security import create_access_token, create_refresh_token, decode_token, generate_salt, hash_password, verify_password
from app.db.models.iam import IAMPermission, IAMRole, IAMSession, IAMUser, IAMUserIdentity, IAMUserRole
from app.db.repositories.iam_repository import IAMRepository
from app.schemas.auth import (
    LoginRequest,
    LoginResponseData,
    LogoutRequest,
    LogoutResponseData,
    MeResponseData,
    RegisterEmailRequest,
    RegisterPhoneRequest,
    RegisterResponse,
    RefreshResponseData,
    RoleBrief,
    SendCodeResponseData,
    SessionProfile,
    UserProfile,
    VerifyCodeResponseData,
    UpdateProfileRequest,
)
from app.services.verification_service import VerificationService
from app.utils.hashing import sha256_text
from app.utils.ids import generate_id

logger = get_logger(__name__)


@dataclass(slots=True)
class AuthContext:
    user: IAMUser
    session: IAMSession
    roles: list[IAMRole]
    permissions: list[IAMPermission]


class AuthService:
    def __init__(self, *, repository: IAMRepository, verification_service: VerificationService, settings: AuthSettings, storage_settings: StorageSettings) -> None:
        self.repository = repository
        self.verification_service = verification_service
        self.settings = settings
        self.storage_settings = storage_settings

    def initialize(self) -> None:
        self.repository.ensure_seed_data(
            bootstrap_password=self.settings.bootstrap_password,
            password_hash_iterations=600000,
            session_ttl_seconds=self.settings.session_ttl_seconds,
        )

    def login(self, payload: LoginRequest) -> LoginResponseData:
        if payload.loginType not in {"username", "phone", "email", "wechat"}:
            raise ContractError("参数错误", status_code=400)
        identity = self.repository.get_identity(payload.loginType, payload.identity)
        if identity is None:
            raise ContractError("用户名或密码错误", status_code=401)
        if not identity.is_enabled:
            raise ContractError("认证方式未启用", status_code=409)
        user = self.repository.get_user_by_id(identity.user_id)
        if user is None:
            raise ContractError("用户不存在", status_code=404)
        if user.status in {"disabled", "locked"}:
            raise ContractError("账号不可用", status_code=403)

        self._validate_identity_credential(identity=identity, login_type=payload.loginType, credential=payload.credential, login_code=payload.loginCode)

        session_id = generate_id("sess")
        access_token = create_access_token(secret=self.settings.jwt_secret, algorithm=self.settings.jwt_algorithm, user_id=user.id, session_id=session_id, expires_in=self.settings.access_token_ttl_seconds)
        refresh_token = create_refresh_token(secret=self.settings.jwt_secret, algorithm=self.settings.jwt_algorithm, user_id=user.id, session_id=session_id, expires_in=self.settings.refresh_token_ttl_seconds)
        session_expired_at = datetime.utcnow() + timedelta(seconds=self.settings.session_ttl_seconds)
        iam_session = self.repository.upsert_session(
            session_id=session_id,
            user_id=user.id,
            identity_id=identity.id,
            login_type=payload.loginType,
            access_token_digest=sha256_text(access_token),
            refresh_token_digest=sha256_text(refresh_token),
            device_type=payload.deviceType,
            device_id=payload.deviceId,
            client_version=payload.clientVersion,
            os_name=payload.osName,
            browser_name=payload.browserName,
            ip_address=payload.ipAddress,
            user_agent=payload.userAgent,
            expired_at=session_expired_at,
        )
        self.repository.touch_user_login(user_id=user.id, ip_address=payload.ipAddress)
        roles = self.repository.get_roles_for_user(user.id)
        logger.info("user login success user_id=%s session_id=%s login_type=%s", user.id, iam_session.session_id, payload.loginType)
        return LoginResponseData(accessToken=access_token, refreshToken=refresh_token, expiresIn=self.settings.access_token_ttl_seconds, sessionId=iam_session.session_id, user=self._to_user_profile(self.repository.get_user_by_id(user.id) or user), roles=[self._to_role_brief(role) for role in roles])

    def logout(self, *, context: AuthContext, payload: LogoutRequest) -> LogoutResponseData:
        session_id = payload.sessionId or context.session.session_id
        iam_session = self.repository.get_session(session_id)
        if iam_session is None:
            raise ContractError("会话不存在", status_code=404)
        if iam_session.user_id != context.user.id:
            raise ContractError("会话不存在", status_code=404)
        if iam_session.session_status != "active":
            raise ContractError("登录已失效", status_code=401)
        updated = self.repository.set_session_status(session_id=session_id, session_status="logout")
        if updated is None:
            raise ContractError("会话不存在", status_code=404)
        return LogoutResponseData(sessionId=updated.session_id, sessionStatus=updated.session_status, logoutAt=self._fmt_dt(updated.logout_at))

    def me(self, *, context: AuthContext) -> MeResponseData:
        return MeResponseData(user=self._to_user_profile(context.user), roles=[self._to_role_brief(role, include_role_type=True) for role in context.roles], permissions=[permission.permission_code for permission in context.permissions], currentSession=SessionProfile(sessionId=context.session.session_id, loginType=context.session.login_type, deviceType=context.session.device_type, loginAt=self._fmt_dt(context.session.login_at), lastActiveAt=self._fmt_dt(context.session.last_active_at), expiredAt=self._fmt_dt(context.session.expired_at), sessionStatus=context.session.session_status, logoutAt=self._fmt_dt(context.session.logout_at), revokeReason=context.session.revoke_reason))

    def update_profile(self, *, context: AuthContext, payload: UpdateProfileRequest) -> UserProfile:
        with self.repository.session_scope() as session:
            # Re-fetch user in current session
            user = session.get(IAMUser, context.user.id)
            if user is None:
                raise ContractError("用户不存在", status_code=404)
            
            if payload.nickname is not None:
                user.nickname = payload.nickname
            if payload.username is not None:
                normalized_username = payload.username.strip()
                user.username = normalized_username or None
            if payload.phone is not None:
                user.phone = payload.phone
            if payload.email is not None:
                user.email = payload.email
            if payload.avatarUrl is not None:
                user.avatar_url = payload.avatarUrl
                
            session.flush()
            # The _to_user_profile needs to format the modified user
            updated_profile = self._to_user_profile(user)
            
        return updated_profile

    def refresh(self, *, refresh_token: str, session_id: str) -> RefreshResponseData:
        iam_session = self.repository.get_session(session_id)
        if iam_session is None:
            raise ContractError("会话不存在", status_code=404)
        if iam_session.session_status != "active":
            raise ContractError("刷新令牌无效或已过期", status_code=401)
        if iam_session.refresh_token_digest != sha256_text(refresh_token):
            raise ContractError("刷新令牌无效或已过期", status_code=401)
        try:
            claims = decode_token(refresh_token, secret=self.settings.jwt_secret, algorithm=self.settings.jwt_algorithm)
        except Exception as exc:
            raise ContractError("刷新令牌无效或已过期", status_code=401) from exc
        if claims.get("typ") != "refresh" or claims.get("sid") != session_id:
            raise ContractError("刷新令牌无效或已过期", status_code=401)
        user_id = int(claims["sub"])
        access_token = create_access_token(secret=self.settings.jwt_secret, algorithm=self.settings.jwt_algorithm, user_id=user_id, session_id=session_id, expires_in=self.settings.access_token_ttl_seconds)
        new_refresh_token = create_refresh_token(secret=self.settings.jwt_secret, algorithm=self.settings.jwt_algorithm, user_id=user_id, session_id=session_id, expires_in=self.settings.refresh_token_ttl_seconds)
        session_expired_at = datetime.utcnow() + timedelta(seconds=self.settings.session_ttl_seconds)
        self.repository.update_session_tokens(session_id=session_id, access_token_digest=sha256_text(access_token), refresh_token_digest=sha256_text(new_refresh_token), expired_at=session_expired_at)
        return RefreshResponseData(accessToken=access_token, refreshToken=new_refresh_token, expiresIn=self.settings.access_token_ttl_seconds, sessionId=session_id)

    def authenticate_access_token(self, token: str) -> AuthContext:
        try:
            claims = decode_token(token, secret=self.settings.jwt_secret, algorithm=self.settings.jwt_algorithm)
        except Exception as exc:
            raise ContractError("未登录或登录已失效", status_code=401) from exc
        if claims.get("typ") != "access":
            raise ContractError("未登录或登录已失效", status_code=401)
        session_id = claims.get("sid")
        user_id = int(claims.get("sub", 0))
        iam_session = self.repository.get_session(session_id)
        if iam_session is None or iam_session.user_id != user_id:
            raise ContractError("未登录或登录已失效", status_code=401)
        expired_at = iam_session.expired_at.replace(tzinfo=timezone.utc) if iam_session.expired_at else None
        if iam_session.session_status != "active" or (expired_at and expired_at < datetime.now(timezone.utc)):
            raise ContractError("未登录或登录已失效", status_code=401)
        if iam_session.access_token_digest != sha256_text(token):
            raise ContractError("未登录或登录已失效", status_code=401)
        user = self.repository.get_user_by_id(user_id)
        if user is None or user.status in {"disabled", "locked"}:
            raise ContractError("未登录或登录已失效", status_code=401)
        roles = self.repository.get_roles_for_user(user_id)
        permissions = self.repository.get_permissions_for_user(user_id)
        return AuthContext(user=user, session=iam_session, roles=roles, permissions=permissions)

    def send_email_code(self, email: str, *, scene: str = "login") -> SendCodeResponseData:
        if scene == "login" and self.repository.get_identity("email", email) is None:
            raise ContractError("邮箱未绑定用户", status_code=404)
        self.verification_service.send_email_code(email, purpose=scene)
        return SendCodeResponseData(
            target=email,
            scene=scene,
            expireSeconds=self.verification_service.settings.code_ttl_seconds,
            debugCode=self.verification_service.settings.mock_fixed_code or None,
        )

    def verify_email_code(self, email: str, code: str, *, scene: str = "login") -> VerifyCodeResponseData:
        self.verification_service.verify_email_code(email, code, purpose=scene)
        return VerifyCodeResponseData(target=email, scene=scene, verified=True)

    def send_sms_code(self, phone: str, *, scene: str = "login") -> SendCodeResponseData:
        if scene == "login" and self.repository.get_identity("phone", phone) is None:
            raise ContractError("手机号未绑定用户", status_code=404)
        self.verification_service.send_sms_code(phone, purpose=scene)
        return SendCodeResponseData(
            target=phone,
            scene=scene,
            expireSeconds=self.verification_service.settings.code_ttl_seconds,
            debugCode=self.verification_service.settings.mock_fixed_code or None,
        )

    def verify_sms_code(self, phone: str, code: str, *, scene: str = "login") -> VerifyCodeResponseData:
        self.verification_service.verify_sms_code(phone, code, purpose=scene)
        return VerifyCodeResponseData(target=phone, scene=scene, verified=True)

    def register_email(self, payload: RegisterEmailRequest) -> RegisterResponse:
        self.verification_service.verify_email_code(payload.email, payload.code, purpose="register")
        return self._register_identity(
            identity_type="email",
            identity_key=payload.email,
            username=payload.username,
            nickname=payload.nickname or payload.email.split("@")[0],
            password=payload.password,
        )

    def register_phone(self, payload: RegisterPhoneRequest) -> RegisterResponse:
        self.verification_service.verify_sms_code(payload.phone, payload.code, purpose="register")
        return self._register_identity(
            identity_type="phone",
            identity_key=payload.phone,
            username=payload.username,
            nickname=payload.nickname or f"用户{payload.phone[-4:]}",
            password=payload.password,
        )

    def _validate_identity_credential(self, *, identity: IAMUserIdentity, login_type: str, credential: str | None, login_code: str | None) -> None:
        if login_type == "wechat":
            if not login_code:
                raise ContractError("认证失败", status_code=401)
            return
        if not credential:
            raise ContractError("认证失败", status_code=401)
        if verify_password(credential, identity.credential_hash, identity.credential_salt, 600000):
            return
        verification_channel = "sms" if login_type == "phone" else "email" if login_type == "email" else None
        if verification_channel and self.verification_service.consume_code(verification_channel, identity.identity_key, credential):
            return
        raise ContractError("用户名或密码错误", status_code=401)

    def _register_identity(self, *, identity_type: str, identity_key: str, username: str | None, nickname: str, password: str | None) -> RegisterResponse:
        with self.repository.session_scope() as session:
            existing = session.scalar(
                select(IAMUserIdentity).where(IAMUserIdentity.identity_type == identity_type, IAMUserIdentity.identity_key == identity_key)
            )
            if existing is not None:
                raise ContractError("账号已存在", status_code=409)

            now = datetime.utcnow()
            next_sequence = (session.scalar(select(func.coalesce(func.max(IAMUser.id), 0))) or 0) + 1
            user = IAMUser(
                user_no=f"U{now.year}{int(next_sequence):04d}",
                username=username,
                nickname=nickname,
                real_name=None,
                avatar_url=None,
                gender=0,
                phone=identity_key if identity_type == "phone" else None,
                email=identity_key if identity_type == "email" else None,
                status="active",
                user_type="normal",
                last_login_at=None,
                last_login_ip=None,
                remark="self_register",
                is_deleted=False,
                created_by=0,
                updated_by=0,
            )
            session.add(user)
            session.flush()

            salt = generate_salt()
            identity = IAMUserIdentity(
                user_id=user.id,
                identity_type=identity_type,
                identity_key=identity_key,
                identity_value=None,
                credential_hash=hash_password(password or self.settings.bootstrap_password, salt, 600000),
                credential_salt=salt,
                verify_status="verified",
                is_primary=True,
                is_enabled=True,
                bound_at=now,
                last_used_at=None,
                expired_at=None,
                extra_data=None,
                remark="self_register",
            )
            session.add(identity)
            session.flush()

            # Assign default 'normal' role
            role = session.scalar(select(IAMRole).where(IAMRole.role_code == "normal", IAMRole.is_deleted.is_(False)))
            if role is not None:
                session.add(IAMUserRole(
                    user_id=user.id,
                    role_id=role.id,
                    assigned_by=0, # System
                    assigned_at=now,
                    status="active",
                    remark="self_register_default"
                ))
            
            session.flush()
            roles = self.repository.get_roles_for_user(user.id)
            return RegisterResponse(user=self._to_user_profile(user), roles=[self._to_role_brief(r) for r in roles], identityType=identity_type, identity=identity_key)

    def _to_user_profile(self, user: IAMUser) -> UserProfile:
        avatar = user.avatar_url
        if avatar and not avatar.startswith("http"):
            scheme = "https" if self.storage_settings.use_ssl else "http"
            url_prefix = f"{scheme}://{self.storage_settings.endpoint}/{self.storage_settings.bucket}/"
            # Prevent double slashes if the path starts with /
            avatar = url_prefix + avatar.lstrip("/")

        return UserProfile(id=user.id, userNo=user.user_no, username=user.username, nickname=user.nickname, realName=user.real_name, avatarUrl=avatar, gender=user.gender, phone=user.phone, email=user.email, status=user.status, userType=user.user_type, lastLoginAt=AuthService._fmt_dt(user.last_login_at), lastLoginIp=user.last_login_ip)

    @staticmethod
    def _to_role_brief(role: IAMRole, *, include_role_type: bool = False) -> RoleBrief:
        return RoleBrief(roleId=role.id, roleCode=role.role_code, roleName=role.role_name, roleType=role.role_type if include_role_type else None)

    @staticmethod
    def _fmt_dt(value: datetime | None) -> str | None:
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else None
