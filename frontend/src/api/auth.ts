import { getJson, postJson } from './client'

export const AUTH_TOKEN_KEY = 'astralith.auth.token'

export interface LoginPayload {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
}

export interface CurrentUser {
  id: number
  username: string
  role: 'admin' | 'user' | string
  is_active: boolean
  created_at: string
  updated_at: string
}

export function getStoredToken(): string | null {
  return localStorage.getItem(AUTH_TOKEN_KEY)
}

export function isAuthenticated(): boolean {
  return getStoredToken() !== null
}

export function storeToken(token: string): void {
  localStorage.setItem(AUTH_TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(AUTH_TOKEN_KEY)
}

export async function login(payload: LoginPayload): Promise<TokenResponse> {
  const token = await postJson<TokenResponse>('/auth/login', payload)
  storeToken(token.access_token)
  return token
}

export function getCurrentUser(): Promise<CurrentUser> {
  return getJson<CurrentUser>('/auth/me')
}
