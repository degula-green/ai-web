import { computed, reactive, readonly } from 'vue'
import { getCurrentUser, login, logout, refreshSession, registerEmail, registerPhone, sendEmailCode, sendSmsCode, updateProfile } from '../api/auth'
import { ApiError, configureAuthTransport } from '../api/http'
import type {
  AuthRoleSummary,
  AuthSessionSummary,
  AuthUserSummary,
  LoginRequestPayload,
  MeResponseData,
  PersistedAuthSession,
  SendCodeResponseData,
} from './types'

const STORAGE_KEY = 'ai-content-auth-session'
const DEFAULT_DEVICE_ID = 'web-browser'

interface AuthState {
  initialized: boolean
  initializing: boolean
  session: PersistedAuthSession | null
  user: AuthUserSummary | null
  roles: AuthRoleSummary[]
  permissions: string[]
  currentSession: AuthSessionSummary | null
}

const state = reactive<AuthState>({
  initialized: false,
  initializing: false,
  session: null,
  user: null,
  roles: [],
  permissions: [],
  currentSession: null,
})

let initPromise: Promise<void> | null = null
let refreshPromise: Promise<PersistedAuthSession | null> | null = null

configureAuthTransport({
  getSession: () => state.session,
  refreshSession: () => authStore.refreshTokens(),
  clearSession: () => authStore.clearSession(),
})

function loadSession() {
  if (state.session) {
    return
  }

  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (!raw) {
    return
  }

  try {
    state.session = JSON.parse(raw) as PersistedAuthSession
  } catch {
    window.localStorage.removeItem(STORAGE_KEY)
  }
}

function persistSession(session: PersistedAuthSession | null) {
  state.session = session

  if (!session) {
    window.localStorage.removeItem(STORAGE_KEY)
    return
  }

  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
}

function applyProfile(payload: MeResponseData) {
  state.user = payload.user
  state.roles = payload.roles
  state.permissions = payload.permissions
  state.currentSession = payload.currentSession
}

function clearProfile() {
  state.user = null
  state.roles = []
  state.permissions = []
  state.currentSession = null
}

function buildDeviceMeta() {
  return {
    deviceType: 'web' as const,
    deviceId: DEFAULT_DEVICE_ID,
    clientVersion: import.meta.env.VITE_APP_VERSION ?? 'dev',
    osName: navigator.platform || 'unknown',
    browserName: detectBrowserName(),
    userAgent: navigator.userAgent,
  }
}

function detectBrowserName() {
  const agent = navigator.userAgent.toLowerCase()
  if (agent.includes('edg')) return 'Edge'
  if (agent.includes('chrome')) return 'Chrome'
  if (agent.includes('safari')) return 'Safari'
  if (agent.includes('firefox')) return 'Firefox'
  return 'Browser'
}

function resolveIdentityType(identity: string): LoginRequestPayload['loginType'] {
  const trimmed = identity.trim()
  if (trimmed.includes('@')) {
    return 'email'
  }

  if (/^\d{11}$/.test(trimmed)) {
    return 'phone'
  }

  return 'username'
}

async function fetchProfile() {
  const data = await getCurrentUser()
  applyProfile(data)
}

export const authStore = {
  state: readonly(state),
  isAuthenticated: computed(() => Boolean(state.session?.accessToken && state.user)),
  displayName: computed(() => state.user?.nickname || state.user?.realName || state.user?.username || '未登录用户'),
  initials: computed(() => {
    const source = state.user?.nickname || state.user?.username || 'U'
    return source.trim().slice(0, 2).toUpperCase()
  }),

  hydrate() {
    loadSession()
  },

  async ensureInitialized() {
    loadSession()

    if (state.initialized) {
      return
    }

    if (initPromise) {
      return initPromise
    }

    state.initializing = true
    initPromise = (async () => {
      if (!state.session) {
        return
      }

      try {
        await fetchProfile()
      } catch {
        const refreshed = await authStore.refreshTokens().catch(() => null)
        if (!refreshed) {
          authStore.clearSession()
          return
        }
        await fetchProfile()
      }
    })()
      .finally(() => {
        state.initialized = true
        state.initializing = false
        initPromise = null
      })

    return initPromise
  },

  async login(identity: string, credential: string) {
    const payload = await login({
      loginType: resolveIdentityType(identity),
      identity: identity.trim(),
      credential: credential.trim(),
      ...buildDeviceMeta(),
    })

    persistSession({
      accessToken: payload.accessToken,
      refreshToken: payload.refreshToken,
      tokenType: payload.tokenType,
      expiresIn: payload.expiresIn,
      sessionId: payload.sessionId,
    })
    state.user = payload.user
    state.roles = payload.roles
    state.permissions = []
    state.currentSession = null
    await fetchProfile()
    state.initialized = true
  },

  async refreshTokens() {
    loadSession()

    if (!state.session?.refreshToken || !state.session.sessionId) {
      return null
    }

    if (refreshPromise) {
      return refreshPromise
    }

    refreshPromise = refreshSession({
      refreshToken: state.session.refreshToken,
      sessionId: state.session.sessionId,
      deviceType: 'web',
      deviceId: DEFAULT_DEVICE_ID,
    })
      .then((payload) => {
        const nextSession: PersistedAuthSession = {
          accessToken: payload.accessToken,
          refreshToken: payload.refreshToken,
          tokenType: payload.tokenType,
          expiresIn: payload.expiresIn,
          sessionId: payload.sessionId,
        }
        persistSession(nextSession)
        return nextSession
      })
      .catch((error) => {
        authStore.clearSession()
        throw error
      })
      .finally(() => {
        refreshPromise = null
      })

    return refreshPromise
  },

  async logout() {
    const sessionId = state.currentSession?.sessionId || state.session?.sessionId

    try {
      if (sessionId) {
        await logout({ sessionId })
      }
    } catch (error) {
      if (!(error instanceof ApiError && error.status === 401)) {
        throw error
      }
    } finally {
      authStore.clearSession()
    }
  },

  clearSession() {
    persistSession(null)
    clearProfile()
    state.initialized = true
  },

  async sendCode(target: string, scene = 'login'): Promise<SendCodeResponseData> {
    const normalizedTarget = target.trim()
    return normalizedTarget.includes('@')
      ? sendEmailCode(normalizedTarget, scene)
      : sendSmsCode(normalizedTarget, scene)
  },

  async register(target: string, code: string, password?: string, nickname?: string) {
    const isEmail = target.includes('@')
    const payload = {
      [isEmail ? 'email' : 'phone']: target.trim(),
      code: code.trim(),
      password: password?.trim(),
      nickname: nickname?.trim(),
    }

    const data = await (isEmail ? registerEmail(payload) : registerPhone(payload))

    // For better UX, attempt auto-login if password was provided during registration
    if (payload.password) {
      try {
        await authStore.login(target, payload.password)
      } catch (loginError) {
        console.warn('Auto-login failed after registration:', loginError)
      }
    }

    return data
  },

  async updateProfile(payload: { nickname?: string; username?: string; phone?: string; email?: string; avatarUrl?: string }) {
    await updateProfile(payload)
    await fetchProfile()
  },

  hasPermission(permission: string) {
    return state.permissions.includes(permission)
  },

  hasAnyPermission(permissions: string[]) {
    if (!permissions.length) {
      return true
    }

    return permissions.some((permission) => state.permissions.includes(permission))
  },
}

export function getAuthErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    return error.message
  }

  if (error instanceof Error) {
    return error.message
  }

  return '请求失败，请稍后重试'
}
