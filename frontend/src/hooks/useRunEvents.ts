import { useEffect, useMemo, useState } from 'react'

export type RunEvent = {
  id: string
  run_id: string
  level: 'info' | 'warn' | 'error'
  agent: string
  type: string
  message: string
  payload: Record<string, unknown>
  created_at: string
}

export function useRunEvents(runId: string | null) {
  const [events, setEvents] = useState<RunEvent[]>([])
  const [connected, setConnected] = useState(false)

  const url = useMemo(() => (runId ? `/api/runs/${runId}/events/stream` : null), [runId])

  useEffect(() => {
    if (!url) return
    setEvents([])
    setConnected(false)
    const es = new EventSource(url)
    es.addEventListener('open', () => setConnected(true))
    es.addEventListener('error', () => setConnected(false))
    es.addEventListener('run_event', (evt) => {
      try {
        const data = JSON.parse((evt as MessageEvent).data) as RunEvent
        setEvents((prev) => [...prev, data].slice(-800))
      } catch {
        return
      }
    })
    return () => es.close()
  }, [url])

  return { events, connected }
}
