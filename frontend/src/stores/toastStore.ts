import { create } from 'zustand'

export type ToastLevel = 'info' | 'success' | 'error'

export type Toast = {
  id: string
  level: ToastLevel
  title: string
  message?: string
}

type ToastState = {
  toasts: Toast[]
  push: (t: Omit<Toast, 'id'>) => void
  dismiss: (id: string) => void
}

function uid() {
  return `${Date.now()}_${Math.random().toString(16).slice(2)}`
}

export const useToastStore = create<ToastState>((set, get) => ({
  toasts: [],
  push: (t) => {
    const id = uid()
    set({ toasts: [{ ...t, id }, ...get().toasts].slice(0, 4) })
    window.setTimeout(() => get().dismiss(id), 4500)
  },
  dismiss: (id) => set({ toasts: get().toasts.filter((x) => x.id !== id) }),
}))
