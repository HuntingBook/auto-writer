import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ChevronRight, Database, Pause, Play, Settings, Square, ArrowLeft, Loader2 } from 'lucide-react'
import DeepSeekModal from '@/components/novel/DeepSeekModal'
import KnowledgeModal from '@/components/novel/KnowledgeModal'
import RunLogPanel from '@/components/novel/RunLogPanel'
import WorkflowSteps from '@/components/novel/WorkflowSteps'
import { api } from '@/utils/api'
import { runKindLabel, runStatusLabel } from '@/utils/labels'
import { useToastStore } from '@/stores/toastStore'
import { cn } from '@/lib/utils'
import type { NovelDetail, Run } from '@/types/novel'

export default function NovelWorkflow() {
  const { novelId } = useParams()
  const nav = useNavigate()
  const toast = useToastStore((s) => s.push)
  const [detail, setDetail] = useState<NovelDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeStep, setActiveStep] = useState<'outline' | 'titles' | 'plan' | 'chapter' | 'reader'>('outline')
  const [activeRun, setActiveRun] = useState<Run | null>(null)

  const [settingsOpen, setSettingsOpen] = useState(false)
  const [knowledgeOpen, setKnowledgeOpen] = useState(false)
  const [apiKey, setApiKey] = useState('')
  const [baseUrl, setBaseUrl] = useState('https://api.deepseek.com')
  const [model, setModel] = useState('deepseek-chat')

  const [outlineDraft, setOutlineDraft] = useState('')

  const canControl = useMemo(() => activeRun && (activeRun.status === 'running' || activeRun.status === 'paused'), [activeRun])

  const refresh = useCallback(async () => {
    if (!novelId) return
    // setLoading(true) // Don't set loading on refresh to avoid flickering
    try {
      const d = await api<NovelDetail>(`/api/novels/${novelId}`)
      setDetail(d)
      if (!outlineDraft && d.latest_outline?.content) {
        setOutlineDraft(d.latest_outline.content)
      } else if (outlineDraft === '' && d.latest_outline?.content) {
        // Initialize draft if empty and remote has content
        setOutlineDraft(d.latest_outline.content)
      }

      setBaseUrl(d.setting.deepseek_base_url || 'https://api.deepseek.com')
      setModel(d.setting.deepseek_model || 'deepseek-chat')
    } catch (e) {
      toast({ level: 'error', title: '加载失败', message: e instanceof Error ? e.message : String(e) })
    } finally {
      setLoading(false)
    }
  }, [novelId, toast]) // Removed outlineDraft dependency to avoid overwrite loop

  useEffect(() => {
    refresh()
  }, [refresh])

  async function startRun(kind: 'outline' | 'titles' | 'plan') {
    if (!novelId) return
    try {
      const r = await api<Run>(`/api/runs/novels/${novelId}/${kind}`, { method: 'POST' })
      setActiveRun(r)
      setActiveRun(r)
    } catch (e) {
      toast({ level: 'error', title: '启动失败', message: e instanceof Error ? e.message : String(e) })
    }
  }

  async function startChapterRun(chapterId: string) {
    if (!novelId) return
    try {
      const r = await api<Run>(`/api/runs/novels/${novelId}/chapter/${chapterId}`, { method: 'POST' })
      setActiveRun(r)
      toast({ level: 'info', title: '已开始逐章生成', message: `Run: ${r.id}` })
    } catch (e) {
      toast({ level: 'error', title: '启动失败', message: e instanceof Error ? e.message : String(e) })
    }
  }

  async function startBatchRun() {
    if (!novelId) return
    try {
      const r = await api<Run>(`/api/runs/novels/${novelId}/chapters/batch`, { method: 'POST', body: JSON.stringify({ only_pending: true }) })
      setActiveRun(r)
      toast({ level: 'info', title: '已开始批量轮询生成', message: `Run: ${r.id}` })
    } catch (e) {
      toast({ level: 'error', title: '启动失败', message: e instanceof Error ? e.message : String(e) })
    }
  }

  async function pause() {
    if (!activeRun) return
    await api(`/api/runs/${activeRun.id}/pause`, { method: 'POST' })
    setActiveRun({ ...activeRun, status: 'paused' })
  }

  async function resume() {
    if (!activeRun) return
    await api(`/api/runs/${activeRun.id}/resume`, { method: 'POST' })
    setActiveRun({ ...activeRun, status: 'running' })
  }

  async function cancel() {
    if (!activeRun) return
    await api(`/api/runs/${activeRun.id}/cancel`, { method: 'POST' })
    setActiveRun({ ...activeRun, status: 'canceled' })
  }

  async function saveOutline() {
    if (!novelId) return
    try {
      await api(`/api/novels/${novelId}/outline`, { method: 'PUT', body: JSON.stringify({ content: outlineDraft }) })
      toast({ level: 'success', title: '已保存新版本大纲' })
      await refresh()
    } catch (e) {
      toast({ level: 'error', title: '保存失败', message: e instanceof Error ? e.message : String(e) })
    }
  }

  async function saveDeepSeekKey() {
    if (!novelId) return
    try {
      await api(`/api/novels/${novelId}/deepseek`, {
        method: 'PUT',
        body: JSON.stringify({ api_key: apiKey, base_url: baseUrl, model }),
      })
      toast({ level: 'success', title: 'DeepSeek 配置已保存' })
      setApiKey('')
      setSettingsOpen(false)
      await refresh()
    } catch (e) {
      toast({ level: 'error', title: '保存失败', message: e instanceof Error ? e.message : String(e) })
    }
  }

  async function saveSelectedTitle(title: string) {
    if (!novelId) return
    try {
      await api(`/api/novels/${novelId}/titles/selection`, { method: 'PUT', body: JSON.stringify({ selected_title: title }) })
      toast({ level: 'success', title: '已设置书名' })
      await refresh()
    } catch (e) {
      toast({ level: 'error', title: '设置失败', message: e instanceof Error ? e.message : String(e) })
    }
  }

  const runId = activeRun?.id || null
  useEffect(() => {
    if (!runId) return
    let timer: number | null = null
    timer = window.setInterval(async () => {
      try {
        const r = await api<Run>(`/api/runs/${runId}`)
        setActiveRun(r)
        if (r.status === 'succeeded' || r.status === 'failed' || r.status === 'canceled') {
          await refresh()
          if (timer) window.clearInterval(timer)
        }
      } catch {
        return
      }
    }, 1200)
    return () => {
      if (timer) window.clearInterval(timer)
    }
  }, [runId, refresh])

  if (loading && !detail) {
    return (
      <div className="min-h-screen bg-[#f8fafc] text-slate-900">
        <div className="mx-auto max-w-7xl px-5 py-8">
          <div className="h-24 animate-pulse rounded-3xl bg-white border border-slate-100 shadow-sm" />
          <div className="mt-6 h-96 animate-pulse rounded-3xl bg-white border border-slate-100 shadow-sm" />
        </div>
      </div>
    )
  }

  if (!detail) {
    return (
      <div className="min-h-screen bg-[#f8fafc] text-slate-900">
        <div className="mx-auto max-w-7xl px-5 py-8">
          <button
            type="button"
            onClick={() => nav('/')}
            className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm border border-slate-200 hover:bg-slate-50 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            返回藏书阁
          </button>
        </div>
      </div>
    )
  }

  /* statusBadge removed */

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-900 pb-10">
      <div className="mx-auto max-w-7xl px-5 py-6">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <button type="button" onClick={() => nav('/')} className="hover:text-slate-900 transition-colors">藏书阁</button>
            <ChevronRight className="h-4 w-4" />
            <span className="text-slate-900 font-semibold">{detail.title}</span>
          </div>
          <div className="flex items-center gap-3">
            {/* statusBadge removed */}

            <button
              type="button"
              onClick={() => setSettingsOpen(true)}
              className="inline-flex items-center gap-2 rounded-xl bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm border border-slate-200 hover:bg-slate-50 hover:text-indigo-600 transition-all"
            >
              <Settings className="h-4 w-4" />
              模型配置
            </button>
            <button
              type="button"
              onClick={() => setKnowledgeOpen(true)}
              className="inline-flex items-center gap-2 rounded-xl bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm border border-slate-200 hover:bg-slate-50 hover:text-indigo-600 transition-all"
            >
              <Database className="h-4 w-4" />
              知识库
            </button>
            {canControl ? (
              <>
                {activeRun?.status === 'running' ? (
                  <button
                    type="button"
                    onClick={pause}
                    className="inline-flex items-center gap-2 rounded-xl bg-amber-500 px-4 py-2 text-sm font-medium text-white shadow-md shadow-amber-200 hover:bg-amber-400 transition-all"
                  >
                    <Pause className="h-4 w-4" />
                    暂停
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={resume}
                    className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-md shadow-blue-200 hover:bg-blue-500 transition-all"
                  >
                    <Play className="h-4 w-4" />
                    继续
                  </button>
                )}
                <button
                  type="button"
                  onClick={cancel}
                  className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm border border-slate-200 hover:bg-red-50 hover:text-red-600 hover:border-red-200 transition-all"
                >
                  <Square className="h-4 w-4" />
                  取消
                </button>
              </>
            ) : null}
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_400px]">
          <WorkflowSteps
            detail={detail}
            activeStep={activeStep}
            setActiveStep={setActiveStep}
            outlineDraft={outlineDraft}
            setOutlineDraft={setOutlineDraft}
            onStartRun={(k) => void startRun(k)}
            onSaveOutline={() => void saveOutline()}
            onSaveSelectedTitle={(t) => void saveSelectedTitle(t)}
            onStartChapterRun={(id) => void startChapterRun(id)}
            onStartChaptersBatchRun={() => void startBatchRun()}
          />

          <RunLogPanel run={activeRun} onRefresh={refresh} />
        </div>
      </div>
      <DeepSeekModal
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        apiKey={apiKey}
        setApiKey={setApiKey}
        baseUrl={baseUrl}
        setBaseUrl={setBaseUrl}
        model={model}
        setModel={setModel}
        onSave={saveDeepSeekKey}
      />
      {novelId ? <KnowledgeModal open={knowledgeOpen} onClose={() => setKnowledgeOpen(false)} novelId={novelId} /> : null}
    </div>
  )
}
