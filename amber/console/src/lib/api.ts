/** API 封装：统一 Base URL + 认证头 + 响应包络解包
 *
 *  后端统一返回 { code, message, data }，本层自动解包出 data。
 *  鉴权失败（401）不再跳转白屏，而是抛出明确错误交由 UI 处理。
 */

const BASE_URL = "/api/v1"

function getApiKey(): string {
  // @ts-ignore
  return import.meta?.env?.VITE_API_KEY || localStorage.getItem("aion_api_key") || ""
}

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let resp: Response
  try {
    resp = await fetch(`${BASE_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": getApiKey(),
        ...(options?.headers || {}),
      },
      ...options,
    })
  } catch (e) {
    throw new ApiError("无法连接后端服务，请检查网络或后端是否已启动", 0)
  }

  if (resp.status === 401) {
    throw new ApiError("认证失败：缺少或未配置有效的 API Key", 401)
  }
  if (!resp.ok) {
    throw new ApiError(`请求失败（HTTP ${resp.status}）`, resp.status)
  }

  const envelope = (await resp.json()) as { code: number; message: string; data?: T }
  if (envelope.code !== 200 && envelope.code !== 0) {
    throw new ApiError(envelope.message || "未知错误", envelope.code)
  }
  return envelope.data as T
}

/** GET 请求（自动拼接 query string） */
export function getJson<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  let url = path
  if (params) {
    const qs = Object.entries(params)
      .filter(([, v]) => v !== undefined && v !== "")
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
      .join("&")
    if (qs) url += `?${qs}`
  }
  return request<T>(url, { method: "GET" })
}

/** POST 请求（JSON body） */
export function postJson<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    body: body ? JSON.stringify(body) : undefined,
  })
}

/** DELETE 请求 */
export function deleteJson<T>(path: string): Promise<T> {
  return request<T>(path, { method: "DELETE" })
}

/** PUT 请求（JSON body） */
export function putJson<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "PUT",
    body: body ? JSON.stringify(body) : undefined,
  })
}
