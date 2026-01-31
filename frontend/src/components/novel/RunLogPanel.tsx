import { AlertTriangle, Cable, CheckCircle2, Clock, Loader2, PauseCircle, XCircle, RotateCcw, ArrowDownCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useRunEvents, type RunEvent } from '@/hooks/useRunEvents'
import { eventTypeLabel, runKindLabel, runStatusLabel, agentLabel } from '@/utils/labels'
import type { Run } from '@/types/novel'
import { useEffect, useMemo, useRef, useState } from 'react'

type Props = {
  run: Run | null
  onRefresh: () => void
}

type Milestone = {
  key: string
  label: string
  done: (events: RunEvent[]) => boolean
}

function hasRunEvent(events: RunEvent[], pred: (e: RunEvent) => boolean): boolean {
  for (const e of events) {
    if (pred(e)) return true
  }
  return false
}

function agentStepDone(agent: string) {
  return (events: RunEvent[]) => hasRunEvent(events, (e) => e.agent === agent && (e.type === 'STEP_OUTPUT' || e.type === 'STEP_FAILED'))
}

function typeDone(type: string) {
  return (events: RunEvent[]) => hasRunEvent(events, (e) => e.type === type)
}

function milestonesForKind(kind: string): Milestone[] {
  if (kind === 'outline') {
    return [
      { key: 'outline', label: '生成大纲', done: agentStepDone('outline_agent') },
      { key: 'bible', label: '初始化设定', done: agentStepDone('bible_agent') },
    ]
  }
  if (kind === 'titles') {
    return [{ key: 'titles', label: '生成书名', done: agentStepDone('title_agent') }]
  }
  if (kind === 'plan') {
    return [{ key: 'plan', label: '生成编排', done: agentStepDone('plan_agent') }]
  }
  if (kind === 'chapter') {
    return [
      { key: 'chapter_outline', label: '章节大纲', done: agentStepDone('chapter_outline_agent') },
      { key: 'chapter_fine_outline', label: '章节细纲', done: agentStepDone('fine_outline_agent') },
      { key: 'chapter_write', label: '正文生成', done: agentStepDone('chapter_writer') },
      { key: 'bible_update', label: '更新设定', done: agentStepDone('bible_agent') },
    ]
  }
  if (kind === 'chapters') {
    return [
      { key: 'batch_start', label: '批量开始', done: typeDone('RUN_STARTED') },
      { key: 'batch_first_done', label: '生成中', done: (events) => hasRunEvent(events, (e) => e.agent === 'chapter_writer' && e.type === 'STEP_OUTPUT') },
      { key: 'batch_all_done', label: '批量完成', done: typeDone('RUN_SUCCEEDED') },
    ]
  }
  return [{ key: 'run', label: '运行中', done: typeDone('RUN_SUCCEEDED') }]
}

export default function RunLogPanel({ run, onRefresh }: Props) {
  const { events, connected } = useRunEvents(run?.id || null)
  const [autoScroll, setAutoScroll] = useState(true)
  const scrollerRef = useRef<HTMLDivElement | null>(null)

  function asArray(v: unknown): unknown[] {
    return Array.isArray(v) ? v : []
  }

  const lastEvent = events.length > 0 ? events[events.length - 1] : null
  const counts = useMemo(() => {
    let info = 0
    let warn = 0
    let error = 0
    for (const e of events) {
      if (e.level === 'error' || e.type === 'STEP_FAILED' || e.type === 'RUN_FAILED') {
        error += 1
      } else if (e.level === 'warn' || e.type === 'STEP_WARN') {
        warn += 1
      } else {
        info += 1
      }
    }
    return { info, warn, error }
  }, [events])

  const stepProgress = useMemo(() => {
    if (!run) return { percent: 0, done: 0, total: 0, current: '' }
    const ms = milestonesForKind(run.kind)
    const total = ms.length
    if (run.status === 'succeeded' || run.status === 'failed' || run.status === 'canceled') {
      return { percent: 100, done: total, total, current: '完成' }
    }
    let done = 0
    for (const m of ms) {
      if (m.done(events)) done += 1
      else break
    }
    const current = done >= total ? '完成' : ms[done]?.label || ''
    const percent = total > 0 ? Math.round((done / total) * 100) : 0
    return { percent, done, total, current }
  }, [events, run])

  const runningHint = useMemo(() => {
    if (!run) return ''
    if (run.status === 'running') {
      if (!connected) return `${stepProgress.done}/${stepProgress.total} · 连接中`
      if (!lastEvent) return `${stepProgress.done}/${stepProgress.total} · 运行中`
      if (lastEvent.type === 'STEP_STARTED') return `${stepProgress.done}/${stepProgress.total} · ${stepProgress.current}`
      return `${stepProgress.done}/${stepProgress.total} · ${eventTypeLabel(lastEvent.type)}`
    }
    if (run.status === 'paused') return `已暂停`
    if (run.status === 'succeeded') return '已完成'
    if (run.status === 'failed') return '失败'
    if (run.status === 'canceled') return '已取消'
    return ''
  }, [connected, lastEvent, run, stepProgress])

  useEffect(() => {
    if (!autoScroll) return
    const el = scrollerRef.current
    if (!el) return
    el.scrollTop = el.scrollHeight
  }, [autoScroll, events.length])

  const statusIcon = useMemo(() => {
    if (!run) return null
    if (run.status === 'running') return <Loader2 className="h-3 w-3 animate-spin text-blue-600" />
    if (run.status === 'paused') return <PauseCircle className="h-3 w-3 text-amber-600" />
    if (run.status === 'succeeded') return <CheckCircle2 className="h-3 w-3 text-emerald-600" />
    if (run.status === 'failed') return <XCircle className="h-3 w-3 text-red-600" />
    if (run.status === 'canceled') return <AlertTriangle className="h-3 w-3 text-slate-500" />
    return null
  }, [run])

  return (
    <div className="rounded-3xl border border-slate-200 bg-white shadow-sm flex flex-col h-full max-h-[800px]">
      <div className="border-b border-slate-100 bg-slate-50/50 px-3 py-2">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Cable className="h-4 w-4 text-indigo-500" />

            <div className="flex items-center text-[10px] font-medium border border-slate-200 rounded-lg bg-white overflow-hidden shadow-sm h-6">
              <div className={cn('px-2 h-full flex items-center gap-1', connected ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-50 text-slate-500')}>
                <div className={cn("w-1.5 h-1.5 rounded-full", connected ? "bg-emerald-500" : "bg-slate-400")} />
                {connected ? '已连接' : '离线'}
              </div>
              {run && (
                <div className="px-2 h-full border-l border-slate-200 flex items-center gap-1 text-slate-700 bg-slate-50/50">
                  {statusIcon}
                  {runKindLabel(run.kind)} : {runStatusLabel(run.status)}
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setAutoScroll((v) => !v)}
              title={autoScroll ? "自动滚动：开" : "自动滚动：关"}
              className={cn('h-6 w-6 flex items-center justify-center rounded-lg transition-colors border', autoScroll ? 'bg-indigo-50 text-indigo-600 border-indigo-200' : 'bg-white text-slate-400 border-transparent hover:bg-slate-100')}
            >
              <ArrowDownCircle className="h-3.5 w-3.5" />
            </button>
            <button
              type="button"
              onClick={onRefresh}
              title="刷新日志"
              className="h-6 w-6 flex items-center justify-center rounded-lg bg-white text-slate-500 hover:bg-slate-100 hover:text-slate-900 transition-colors border border-transparent hover:border-slate-200"
            >
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {run ? (
          <div className="mt-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-[10px] text-slate-400 font-mono scale-90 origin-left">{runningHint || '...'}</div>
            </div>
            <div className="mt-1 h-1 overflow-hidden rounded-full bg-slate-100">
              <div
                className={cn(
                  'h-full rounded-full transition-[width] duration-300',
                  run.status === 'failed' ? 'bg-red-500' : run.status === 'canceled' ? 'bg-slate-400' : 'bg-indigo-500'
                )}
                style={{ width: `${stepProgress.percent}%` }}
              />
            </div>
            <div className="mt-2 flex items-center justify-end gap-3 text-[10px] font-mono">
              <span className="text-slate-400">信息 {counts.info}</span>
              <span className={cn(counts.warn > 0 ? "text-amber-600 font-bold" : "text-slate-300")}>警告 {counts.warn}</span>
              <span className={cn(counts.error > 0 ? "text-red-600 font-bold" : "text-slate-300")}>错误 {counts.error}</span>
            </div>
          </div>
        ) : null}
      </div>

      <div ref={scrollerRef} className="flex-1 overflow-auto p-3 bg-slate-50/30 scrollbar-thin">
        {events.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-xs text-slate-400">
            {run?.status === 'running' ? <Loader2 className="h-4 w-4 animate-spin text-indigo-400" /> : <div className="p-2 bg-slate-100 rounded-full"><Cable className="h-4 w-4 text-slate-300" /></div>}
            <div>{run?.status === 'running' ? (connected ? '运行中...' : '连接中...') : '暂无日志'}</div>
          </div>
        ) : (
          <div className="space-y-2 font-mono text-xs">
            {events.map((e) => (
              <div key={e.id} className="rounded-lg border border-slate-200 bg-white p-2.5 shadow-sm">
                <div className="flex items-center justify-between gap-2 mb-1 opacity-70">
                  <div className="truncate font-bold text-slate-700 flex items-center gap-1.5">
                    <span className="px-1 py-0.5 bg-slate-100 rounded text-[10px] text-slate-600">{agentLabel(e.agent)}</span>
                    <span className="text-slate-300">·</span>
                    <span className="text-[10px]">{eventTypeLabel(e.type)}</span>
                  </div>
                  <div className="text-[10px] text-slate-300 tabular-nums">
                    {new Date(e.created_at).toLocaleTimeString()}
                  </div>
                </div>
                <div className={cn(
                  'text-xs leading-relaxed break-words',
                  (e.level === 'error' || e.type === 'STEP_FAILED' || e.type === 'RUN_FAILED') ? 'text-red-700' :
                    (e.level === 'warn' || e.type === 'STEP_WARN') ? 'text-amber-700' :
                      'text-slate-600'
                )}>
                  {e.message}
                </div>
                {e.payload?.preview ? (
                  <div className="mt-1.5 whitespace-pre-wrap rounded bg-slate-50 p-2 text-[10px] text-slate-500 border border-slate-100 leading-normal">
                    {String(e.payload.preview)}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
