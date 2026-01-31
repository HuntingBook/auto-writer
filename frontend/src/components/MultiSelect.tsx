import { ChevronDown, Check, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { cn } from '@/lib/utils'

type Option = {
  value: string
  label: string
}

type Props = {
  label: string
  placeholder?: string
  value: string[]
  options: Option[]
  onChange: (next: string[]) => void
}

export default function MultiSelect({ label, placeholder, value, options, onChange }: Props) {
  const [open, setOpen] = useState(false)
  const [q, setQ] = useState('')

  const filtered = useMemo(() => {
    const query = q.trim().toLowerCase()
    if (!query) return options
    return options.filter((o) => o.label.toLowerCase().includes(query) || o.value.toLowerCase().includes(query))
  }, [options, q])

  const selectedSet = useMemo(() => new Set(value), [value])

  function toggle(v: string) {
    const next = new Set(value)
    if (next.has(v)) next.delete(v)
    else next.add(v)
    onChange(Array.from(next))
  }

  function remove(v: string) {
    onChange(value.filter((x) => x !== v))
  }

  return (
    <div className="space-y-2 relative">
      <div className="text-xs font-medium text-zinc-700">{label}</div>
      <button
        type="button"
        onClick={() => setOpen((s) => !s)}
        className="flex w-full items-center justify-between rounded-xl border border-zinc-200 bg-white px-3 py-2 text-left text-sm text-zinc-900 hover:bg-zinc-50"
      >
        <span className={cn('truncate', value.length === 0 && 'text-zinc-500')}>
          {value.length === 0 ? (placeholder || '请选择') : `${value.length} 项已选`}
        </span>
        <ChevronDown className={cn('h-4 w-4 text-zinc-500 transition-transform', open && 'rotate-180')} />
      </button>

      {value.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {value.map((v) => (
            <span key={v} className="inline-flex items-center gap-1 rounded-full bg-zinc-100 px-2 py-1 text-xs text-zinc-800">
              {v}
              <button
                type="button"
                onClick={() => remove(v)}
                className="rounded-full p-0.5 text-zinc-500 hover:bg-zinc-200 hover:text-zinc-900"
                aria-label="移除"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}
        </div>
      ) : null}

      {open ? (
        <div className="absolute z-50 top-full mt-2 w-full rounded-2xl border border-zinc-200 bg-white p-2 shadow-xl">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="w-full rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400"
            placeholder="搜索"
          />
          <div className="mt-2 max-h-56 overflow-auto">
            {filtered.length === 0 ? (
              <div className="px-3 py-8 text-center text-sm text-zinc-500">无匹配选项</div>
            ) : (
              filtered.map((o) => (
                <button
                  key={o.value}
                  type="button"
                  onClick={() => toggle(o.value)}
                  className="flex w-full items-center justify-between rounded-xl px-3 py-2 text-sm text-zinc-900 hover:bg-zinc-100"
                >
                  <span className="truncate">{o.label}</span>
                  {selectedSet.has(o.value) ? <Check className="h-4 w-4 text-emerald-600" /> : <span className="h-4 w-4" />}
                </button>
              ))
            )}
          </div>
          <div className="mt-2 flex justify-end">
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="rounded-lg bg-zinc-100 px-3 py-2 text-sm text-zinc-900 hover:bg-zinc-200"
            >
              完成
            </button>
          </div>
        </div>
      ) : null}
    </div>
  )
}
