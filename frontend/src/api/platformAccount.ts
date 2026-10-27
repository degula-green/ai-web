import { request } from './http'

const COOKIE_BRIDGE_EXTENSION_DOWNLOAD_URL =
  import.meta.env.VITE_COOKIE_BRIDGE_EXTENSION_DOWNLOAD_URL?.trim() ||
  'http://47.115.216.167:9090/api/v1/download-shared-object/aHR0cDovLzEyNy4wLjAuMTo5MDgwL2FpY29udGVudC9leHRlbnNpb24uemlwP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9OTZWWFQ5OUFZTTJGQVZOWEQ3MzAlMkYyMDI2MDQxNyUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNjA0MTdUMDQyMTU0WiZYLUFtei1FeHBpcmVzPTQzMjAwJlgtQW16LVNlY3VyaXR5LVRva2VuPWV5SmhiR2NpT2lKSVV6VXhNaUlzSW5SNWNDSTZJa3BYVkNKOS5leUpoWTJObGMzTkxaWGtpT2lJNU5sWllWRGs1UVZsTk1rWkJWazVZUkRjek1DSXNJbVY0Y0NJNk1UYzNOalEwTWpVMk5Dd2ljR0Z5Wlc1MElqb2liV2x1YVc5aFpHMXBiaUo5Ll9uY3RNVWlWa0VzUEpwU29Qb1l5X0xtSGk5bUY1MkZiS21JRDhORDNXZ3pJbjBLNGhTNHFxRWdwSE02cGtwekIwMVo2cXJ2TFhEUDBpNGt1RVkzT3JBJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCZ2ZXJzaW9uSWQ9bnVsbCZYLUFtei1TaWduYXR1cmU9Zjg1NDYzZmQyZmRiNzY1NjJkYWM1M2MxNDAxNzYwOGY5ODY2ZTM5ODYxMGU4YTVmMTJiMzJjYmI4M2UzNzFhNw'

export interface AccountShortInfo {
  accountId: number
  platformCode: string
  accountName?: string
  nickname?: string
  avatarUrl?: string
  platformUid?: string
  authStatus: string
  sessionStatus?: string
  expiresAt?: string | null
  lastSyncAt?: string
}

export interface AccountListResponse {
  list: AccountShortInfo[]
  total: number
}

export interface UnbindResponse {
  accountId: number
  unbindAt: string
}

export interface AuthHistoryItem {
  id: number
  platformCode: string
  accountName?: string
  eventType: string
  eventStatus: string
  failReason?: string
  createdAt: string
}

export interface AuthHistoryResponse {
  list: AuthHistoryItem[]
  total: number
}

export interface CookieBridgeClientInfo {
  clientId: string
  connected: boolean
  nicknames: Record<string, string>
  platforms: Record<string, any>
  connectedAt?: number | null
  lastSeen?: number | null
}

export interface CookieBridgeAccountsResponse {
  list: CookieBridgeClientInfo[]
  total: number
  bridgeUrl: string
}

export interface CookieBridgeBindPayload {
  platformCode: string
  clientId: string
  setDefault?: boolean
}

export interface CookieBridgeBindResponse {
  accountId: number
  crawlerCookieAccountId: number
  bridgeClientId: string
  platformCode: string
  syncedAt: string
}

export interface SyncSelfWorksResponse {
  accountId: number
  platformCode: string
  secUserId: string
  syncedCount: number
  relationCount: number
  duplicatedCount: number
  creatorSaved: boolean
  awemeIds: string[]
}

export const platformAccountApi = {
  listAccounts(platformCode?: string) {
    const query = platformCode ? `?platformCode=${encodeURIComponent(platformCode)}` : ''
    return request<AccountListResponse>(`/api/v1/platforms/accounts${query}`, {
      method: 'GET',
    })
  },
  unbindAccount(accountId: number) {
    return request<UnbindResponse>(`/api/v1/platforms/accounts/${accountId}`, {
      method: 'DELETE',
    })
  },
  syncSelfWorks(accountId: number, maxCount = 50) {
    return request<SyncSelfWorksResponse>(`/api/v1/platforms/accounts/${accountId}/sync-self-works`, {
      method: 'POST',
      body: { maxCount },
    })
  },
  getAuthHistory() {
    return request<AuthHistoryResponse>('/api/v1/platforms/auth/history', {
      method: 'GET',
    })
  },
  listCookieBridgeAccounts() {
    return request<CookieBridgeAccountsResponse>('/api/v1/platforms/cookie-bridge/accounts', {
      method: 'GET',
    })
  },
  bindCookieBridgeClient(data: CookieBridgeBindPayload) {
    return request<CookieBridgeBindResponse>('/api/v1/platforms/cookie-bridge/bind', {
      method: 'POST',
      body: data,
    })
  },
  getCookieBridgeExtensionDownloadUrl() {
    return COOKIE_BRIDGE_EXTENSION_DOWNLOAD_URL
  },
}
