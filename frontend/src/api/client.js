const NETWORK_ERROR = '서버에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.'

// Every call resolves to { ok, status, data } and never throws, so screens handle one shape.
// Server errors arrive as data.detail = { message, fields? }.
// A FormData body (file upload) is sent as-is so the browser sets the multipart header.
export async function apiRequest(path, { method = 'GET', body } = {}) {
  const isJson = body !== undefined && !(body instanceof FormData)
  try {
    const response = await fetch(path, {
      method,
      credentials: 'same-origin',
      headers: isJson ? { 'Content-Type': 'application/json' } : undefined,
      body: isJson ? JSON.stringify(body) : body,
    })
    const data = response.status === 204 ? null : await response.json().catch(() => null)
    // 502-504 without our JSON body: the dev proxy (or a gateway) could not reach the API server.
    if (response.status >= 502 && response.status <= 504 && data?.detail === undefined) {
      return { ok: false, status: response.status, data: { detail: { message: NETWORK_ERROR } } }
    }
    return { ok: response.ok, status: response.status, data }
  } catch {
    return { ok: false, status: 0, data: { detail: { message: NETWORK_ERROR } } }
  }
}

export function errorMessage(result) {
  return result.data?.detail?.message ?? '요청을 처리하지 못했습니다. 다시 시도해 주세요.'
}

export function fieldErrors(result) {
  return result.data?.detail?.fields ?? {}
}
