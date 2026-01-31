import { X } from 'lucide-react'
import { useToastStore } from '@/stores/toastStore'
import { cn } from '@/lib/utils'

export default function ToastViewport() {
  const { toasts, dismiss } = useToastStore()

  return (
    <div className="pointer-events-none fixed right-4 top-4 z-50 flex w-[360px] flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={cn(
            'pointer-events-auto rounded-xl border bg-white/95 p-3 shadow-lg backdrop-blur dark:border-white/10 dark:bg-zinc-950/90',
            t.level === 'error' && 'border-red-200 dark:border-red-900/40',
            t.level === 'success' && 'border-emerald-200 dark:border-emerald-900/40'
          )}
        >
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <div className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">{t.title}</div>
              {t.message ? <div className="mt-0.5 text-sm text-zinc-600 dark:text-zinc-300">{t.message}</div> : null}
            </div>
            <button
              type="button"
              onClick={() => dismiss(t.id)}
              className="rounded-md p-1 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-800 dark:hover:bg-white/10 dark:hover:text-zinc-100"
              aria-label="关闭"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
