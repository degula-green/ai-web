export interface AuthUserSummary {
  id: number
  userNo: string
  username: string | null
  nickname: string
  realName: string | null
  avatarUrl: string | null
  gender: number
  phone: string | null
  email: string | null
  status: string
  userType: string
  lastLoginAt: string | null
  lastLoginIp: string | null
}

export interface AuthRoleSummary {
  roleId: number
  roleCode: string
  roleName: string
  roleType?: string | null
}

export interface AuthSessionSummary {
  sessionId: string
  loginType: string
  deviceType: string
  loginAt: string
  lastActiveAt: string | null
  expiredAt: string | null
  sessionStatus: string
  logoutAt: string | null
  revokeReason?: string | null
}

export interface LoginRequestPayload {
  loginType: 'username' | 'phone' | 'email' | 'wechat'
  identity: string
  credential?: string
  loginCode?: string
  deviceType: 'web' | 'mobile' | 'miniapp'
  deviceId?: string
  clientVersion?: string
  osName?: string
  browserName?: string
  userAgent?: string
  ipAddress?: string
}

export interface LoginResponseData {
  accessToken: string
  refreshToken: string
  tokenType: string
  expiresIn: number
  sessionId: string
  user: AuthUserSummary
  roles: AuthRoleSummary[]
}

export interface MeResponseData {
  user: AuthUserSummary
  roles: AuthRoleSummary[]
  permissions: string[]
  currentSession: AuthSessionSummary
}

export interface RefreshRequestPayload {
  refreshToken: string
  sessionId: string
  deviceType?: string
  deviceId?: string
}

export interface RefreshResponseData {
  accessToken: string
  refreshToken: string
  tokenType: string
  expiresIn: number
  sessionId: string
}

export interface LogoutRequestPayload {
  sessionId?: string
}

export interface LogoutResponseData {
  sessionId: string
  sessionStatus: string
  logoutAt: string | null
}

export interface SendCodeResponseData {
  target: string
  scene: string
  expireSeconds: number
  debugCode?: string | null
}

export interface VerifyCodeResponseData {
  target: string
  scene: string
  verified: boolean
}

export interface RegisterRequestPayload {
  email?: string
  phone?: string
  code: string
  password?: string
  username?: string
  nickname?: string
  realName?: string
}

export interface RegisterResponseData {
  user: AuthUserSummary
  roles: AuthRoleSummary[]
  identityType: string
  identity: string
}

export interface UpdateProfileRequestPayload {
  nickname?: string
  username?: string
  phone?: string
  email?: string
  avatarUrl?: string
}

export interface SendCodeRequestPayload {
  email?: string
  phone?: string
  scene?: string
}

export interface PersistedAuthSession {
  accessToken: string
  refreshToken: string
  tokenType: string
  expiresIn: number
  sessionId: string
}
