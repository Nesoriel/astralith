const API_BASE = '/api/v1'

export async function requestJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  // 统一封装 JSON 请求，后续可在这里加入 token、错误提示和刷新登录逻辑。
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...init.headers,
    },
    ...init,
  })
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`)
  }
  if (response.status === 204) {
    return undefined as T
  }
  return response.json() as Promise<T>
}

export function getJson<T>(path: string): Promise<T> {
  return requestJson<T>(path)
}

export function postJson<T>(path: string, body?: unknown): Promise<T> {
  return requestJson<T>(path, {
    method: 'POST',
    body: body === undefined ? undefined : JSON.stringify(body),
  })
}

export function putJson<T>(path: string, body: unknown): Promise<T> {
  return requestJson<T>(path, {
    method: 'PUT',
    body: JSON.stringify(body),
  })
}

export function deleteJson(path: string): Promise<void> {
  return requestJson<void>(path, { method: 'DELETE' })
}
