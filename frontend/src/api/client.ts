const API_BASE = '/api/v1'

// 统一封装 JSON GET 请求，后续可在这里加入 token、错误提示和刷新登录逻辑。
export async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`)
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}
