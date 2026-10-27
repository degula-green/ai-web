import type { PersistedAuthSession } from '../auth/types'

export interface ApiEnvelope<T> {
  code: number
  msg: string
  data: T
}

export class ApiError extends Error {
  code: number
  status: number
  data: unknown

  constructor(message: string, options: { code: number; status: number; data?: unknown }) {
    super(message)
    this.name = 'ApiError'
    this.code = options.code
    this.status = options.status
    this.data = options.data ?? null
  }
}

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown
  auth?: boolean
  retryOnUnauthorized?: boolean
}

interface AuthTransportHandlers {
  getSession: () => PersistedAuthSession | null
  refreshSession: () => Promise<PersistedAuthSession | null>
  clearSession: () => void
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '')

let authHandlers: AuthTransportHandlers | null = null

export function getApiBaseUrl() {
  return API_BASE_URL
}

export function configureAuthTransport(handlers: AuthTransportHandlers) {
  authHandlers = handlers
}

export async function rawRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  return executeRequest<T>(path, options)
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  return executeRequest<T>(path, { auth: true, retryOnUnauthorized: true, ...options })
}

async function executeRequest<T>(path: string, options: RequestOptions): Promise<T> {
  const { auth = false, retryOnUnauthorized = false, headers, body, ...rest } = options
  const nextHeaders = new Headers(headers ?? {})

  const isFormData = body instanceof FormData

  if (body !== undefined && !isFormData && !nextHeaders.has('Content-Type')) {
    nextHeaders.set('Content-Type', 'application/json')
  }

  if (auth) {
    const session = authHandlers?.getSession()
    if (session?.accessToken) {
      nextHeaders.set('Authorization', `Bearer ${session.accessToken}`)
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: nextHeaders,
    body: body === undefined ? undefined : (isFormData ? (body as FormData) : JSON.stringify(body)),
  })

  const payload = await parseJson<ApiEnvelope<T>>(response)

  if (response.status === 401 && auth && retryOnUnauthorized && authHandlers) {
    const refreshedSession = await authHandlers.refreshSession().catch(() => {
      authHandlers?.clearSession()
      return null
    })

    if (refreshedSession?.accessToken) {
      return executeRequest<T>(path, { ...options, retryOnUnauthorized: false })
    }
  }

  if (!response.ok) {
    throw new ApiError(payload?.msg ?? `Request failed with status ${response.status}`, {
      code: payload?.code ?? response.status,
      status: response.status,
      data: payload?.data,
    })
  }

  if (!payload) {
    throw new ApiError('接口返回为空', {
      code: response.status,
      status: response.status,
    })
  }

  if (typeof payload.code !== 'number' || payload.code < 200 || payload.code >= 300) {
    throw new ApiError(payload.msg || '接口调用失败', {
      code: payload.code ?? response.status,
      status: response.status,
      data: payload.data,
    })
  }

  return payload.data
}

async function parseJson<T>(response: Response): Promise<T | null> {
  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('application/json')) {
    return null
  }

  return response.json() as Promise<T>
}
