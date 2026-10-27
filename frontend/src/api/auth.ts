import type {
  LoginRequestPayload,
  LoginResponseData,
  LogoutRequestPayload,
  LogoutResponseData,
  MeResponseData,
  RefreshRequestPayload,
  RefreshResponseData,
  SendCodeResponseData,
  VerifyCodeResponseData,
  RegisterRequestPayload,
  RegisterResponseData,
  UpdateProfileRequestPayload,
} from '../auth/types'
import { rawRequest, request } from './http'

export function login(payload: LoginRequestPayload) {
  return rawRequest<LoginResponseData>('/api/v1/auth/login', {
    method: 'POST',
    body: payload,
  })
}

export function logout(payload: LogoutRequestPayload) {
  return request<LogoutResponseData>('/api/v1/auth/logout', {
    method: 'POST',
    body: payload,
    retryOnUnauthorized: false,
  })
}

export function getCurrentUser() {
  return request<MeResponseData>('/api/v1/auth/me', {
    method: 'GET',
  })
}

export function updateProfile(payload: UpdateProfileRequestPayload) {
  return request<{ msg: string }>('/api/v1/auth/me', {
    method: 'PATCH',
    body: payload,
  })
}

export function uploadAvatar(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return request<{ url: string }>('/api/v1/auth/avatar/upload', {
    method: 'POST',
    body: formData,
    // When fetch sees FormData, it automatically sets the Content-Type with formData boundary,
    // but our http client might wrap it in JSON. Let's make sure our http.ts handles FormData correctly.
  })
}

export function refreshSession(payload: RefreshRequestPayload) {
  return rawRequest<RefreshResponseData>('/api/v1/auth/refresh', {
    method: 'POST',
    body: payload,
  })
}

export function sendEmailCode(email: string, scene = 'login') {
  return rawRequest<SendCodeResponseData>('/api/v1/auth/email/send-code', {
    method: 'POST',
    body: { email, scene },
  })
}

export function verifyEmailCode(email: string, code: string, scene = 'login') {
  return rawRequest<VerifyCodeResponseData>('/api/v1/auth/email/verify-code', {
    method: 'POST',
    body: { email, code, scene },
  })
}

export function sendSmsCode(phone: string, scene = 'login') {
  return rawRequest<SendCodeResponseData>('/api/v1/auth/sms/send-code', {
    method: 'POST',
    body: { phone, scene },
  })
}

export function verifySmsCode(phone: string, code: string, scene = 'login') {
  return rawRequest<VerifyCodeResponseData>('/api/v1/auth/sms/verify-code', {
    method: 'POST',
    body: { phone, code, scene },
  })
}
export function registerEmail(payload: RegisterRequestPayload) {
  return rawRequest<RegisterResponseData>('/api/v1/auth/register/email', {
    method: 'POST',
    body: payload,
  })
}

export function registerPhone(payload: RegisterRequestPayload) {
  return rawRequest<RegisterResponseData>('/api/v1/auth/register/phone', {
    method: 'POST',
    body: payload,
  })
}
