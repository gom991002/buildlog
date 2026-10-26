const NETWORK_ERROR = '서버에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.'

// Every call resolves to { ok, status, data } and never throws, so screens handle one shape.
// Server errors arrive as data.detail = { message, fields? }.
export async function apiRequest(path, { method = 'GET', body } = {}) {
  try {
    const response = await fetch(path, {
      method,
      credentials: 'same-origin',
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
    const data = response.status === 204 ? null : await response.json().catch(() => null)
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
