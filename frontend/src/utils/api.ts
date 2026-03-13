declare global {
  interface Window {
    AUTO_WRITER_API_BASE_URL?: string
  }
}

export class ApiError extends Error {
  status: number
  payload: unknown

  constructor(message: string, status: number, payload: unknown) {
    super(message)
    this.status = status
    this.payload = payload
  }
}

async function parseJsonSafe(res: Response): Promise<unknown> {
  const text = await res.text()
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

function getApiBase(): string {
  return window.AUTO_WRITER_API_BASE_URL || ''
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const base = getApiBase()
  const url = base ? `${base}${path}` : path
  const res = await fetch(url, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
  })

  if (!res.ok) {
    const payload = await parseJsonSafe(res)
    const msg =
      typeof payload === 'object' && payload !== null &&
      'detail' in payload && typeof (payload as Record<string, unknown>).detail === 'string'
        ? String((payload as Record<string, unknown>).detail)
        : res.statusText
    throw new ApiError(msg || 'Request failed', res.status, payload)
  }

  return (await parseJsonSafe(res)) as T
}
