from __future__ import annotations

from pydantic import BaseModel, Field


class AuthUserSummary(BaseModel):
    id: int
    userNo: str
    username: str | None = None
    nickname: str
    realName: str | None = None
    avatarUrl: str | None = None
    gender: int = 0
    phone: str | None = None
    email: str | None = None
    status: str
    userType: str
    lastLoginAt: str | None = None
    lastLoginIp: str | None = None


class AuthRoleSummary(BaseModel):
    roleId: int
    roleCode: str
    roleName: str
    roleType: str | None = None


class AuthPermissionSummary(BaseModel):
    permissionId: int
    permissionCode: str
    permissionName: str


class AuthSessionSummary(BaseModel):
    sessionId: str
    loginType: str
    deviceType: str
    loginAt: str
    lastActiveAt: str | None = None
    expiredAt: str | None = None
    sessionStatus: str
    logoutAt: str | None = None
    revokeReason: str | None = None


class LoginRequest(BaseModel):
    loginType: str
    identity: str
    credential: str | None = None
    loginCode: str | None = None
    deviceType: str = "web"
    deviceId: str | None = None
    clientVersion: str | None = None
    osName: str | None = None
    browserName: str | None = None
    userAgent: str | None = None
    ipAddress: str | None = None


class LoginResponse(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str = "Bearer"
    expiresIn: int
    sessionId: str
    user: AuthUserSummary
    roles: list[AuthRoleSummary]


class LogoutRequest(BaseModel):
    sessionId: str | None = None


class LogoutResponse(BaseModel):
    sessionId: str
    sessionStatus: str
    logoutAt: str | None = None


class MeResponse(BaseModel):
    user: AuthUserSummary
    roles: list[AuthRoleSummary]
    permissions: list[str]
    currentSession: AuthSessionSummary


class RefreshRequest(BaseModel):
    refreshToken: str
    sessionId: str
    deviceType: str | None = None
    deviceId: str | None = None


class RefreshResponse(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str = "Bearer"
    expiresIn: int
    sessionId: str


class SendEmailCodeRequest(BaseModel):
    email: str
    scene: str = "login"


class VerifyEmailCodeRequest(BaseModel):
    email: str
    code: str
    scene: str = "login"


class SendSmsCodeRequest(BaseModel):
    phone: str
    scene: str = "login"


class VerifySmsCodeRequest(BaseModel):
    phone: str
    code: str
    scene: str = "login"


class VerificationResponse(BaseModel):
    target: str
    scene: str
    expireSeconds: int
    debugCode: str | None = None


class VerificationCheckResponse(BaseModel):
    target: str
    scene: str
    verified: bool


class RegisterEmailRequest(BaseModel):
    email: str
    code: str
    password: str | None = None
    username: str | None = None
    nickname: str | None = None
    realName: str | None = None


class RegisterPhoneRequest(BaseModel):
    phone: str
    code: str
    password: str | None = None
    username: str | None = None
    nickname: str | None = None
    realName: str | None = None


class RegisterResponse(BaseModel):
    user: AuthUserSummary
    roles: list[AuthRoleSummary] = Field(default_factory=list)
    identityType: str
    identity: str


class UpdateProfileRequest(BaseModel):
    nickname: str | None = Field(default=None, max_length=64)
    username: str | None = Field(default=None, max_length=64)
    phone: str | None = Field(default=None, max_length=32, description="If provided, binds the phone number")
    email: str | None = Field(default=None, max_length=128, description="If provided, binds the email")
    avatarUrl: str | None = Field(default=None, max_length=1024, description="If provided, updates the user's avatar URL")


RoleSummary = AuthRoleSummary
RoleBrief = AuthRoleSummary
PermissionBrief = AuthPermissionSummary
UserProfile = AuthUserSummary
SessionProfile = AuthSessionSummary
LoginResponseData = LoginResponse
LogoutResponseData = LogoutResponse
MeResponseData = MeResponse
RefreshTokenRequest = RefreshRequest
RefreshResponseData = RefreshResponse
SendCodeResponseData = VerificationResponse
VerifyCodeResponseData = VerificationCheckResponse
RegisterResponseData = RegisterResponse
