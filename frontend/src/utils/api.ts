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

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
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
