import { useMemo, useState } from 'react'
import Modal from '@/components/Modal'
import { api } from '@/utils/api'
import { useToastStore } from '@/stores/toastStore'

type Doc = {
  id: string
  title: string
  source: string
  source_uri?: string | null
  content: string
  created_at: string
  updated_at: string
}

type Props = {
  open: boolean
  onClose: () => void
  novelId: string
}

export default function KnowledgeModal({ open, onClose, novelId }: Props) {
  const toast = useToastStore((s) => s.push)
  const [tab, setTab] = useState<'upload' | 'url' | 'search'>('upload')
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [url, setUrl] = useState('')
  const [search, setSearch] = useState('')
  const [results, setResults] = useState<Doc[]>([])
  const [busy, setBusy] = useState(false)

  const canUpload = useMemo(() => content.trim().length > 20, [content])
  const canUrl = useMemo(() => url.trim().startsWith('http'), [url])

  async function addText() {
    if (!canUpload || busy) return
    setBusy(true)
    try {
      await api(`/api/novels/${novelId}/knowledge/docs`, {
        method: 'POST',
        body: JSON.stringify({ title: title.trim() || undefined, content }),
      })
      toast({ level: 'success', title: '已入库', message: '资料已保存到知识库' })
      setTitle('')
      setContent('')
      setTab('search')
      await doSearch('')
    } catch (e) {
      toast({ level: 'error', title: '入库失败', message: e instanceof Error ? e.message : String(e) })
    } finally {
      setBusy(false)
    }
  }

  async function addUrl() {
    if (!canUrl || busy) return
    setBusy(true)
    try {
      await api(`/api/novels/${novelId}/knowledge/url`, {
        method: 'POST',
        body: JSON.stringify({ url: url.trim(), title: title.trim() || undefined }),
      })
      toast({ level: 'success', title: '已抓取并入库', message: url.trim() })
      setTitle('')
      setUrl('')
      setTab('search')
      await doSearch('')
    } catch (e) {
      toast({ level: 'error', title: '抓取失败', message: e instanceof Error ? e.message : String(e) })
    } finally {
      setBusy(false)
    }
  }

  async function doSearch(q: string) {
    try {
      const res = await api<Doc[]>(`/api/novels/${novelId}/knowledge/search?q=${encodeURIComponent(q)}`)
      setResults(res)
    } catch (e) {
      toast({ level: 'error', title: '搜索失败', message: e instanceof Error ? e.message : String(e) })
    }
  }

  return (
    <Modal title="知识库管理" open={open} onClose={onClose}>
      <div className="bg-slate-100 p-1 rounded-xl flex mb-4">
        {[
          { key: 'upload', label: '手动录入' },
          { key: 'url', label: '网页抓取' },
          { key: 'search', label: '检索资料' },
        ].map((item) => (
          <button
            key={item.key}
            type="button"
            onClick={() => {
              setTab(item.key as any)
              if (item.key === 'search') void doSearch(search)
            }}
            className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${tab === item.key
                ? 'bg-white text-indigo-600 shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
              }`}
          >
            {item.label}
          </button>
        ))}
      </div>

      <div className="space-y-4">
        <div>
          <div className="text-xs font-semibold text-slate-700 mb-1.5">资料标题 (可选)</div>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition-all"
            placeholder="例如：世界观设定补充 / 人物小传..."
          />
        </div>

        {tab === 'upload' ? (
          <div>
            <div className="text-xs font-semibold text-slate-700 mb-1.5">文本内容</div>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="h-48 w-full resize-none rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition-all leading-relaxed"
              placeholder="请粘贴设定资料、参考文本等..."
            />
            <div className="mt-4 flex justify-end gap-3">
              <button type="button" onClick={onClose} className="rounded-xl bg-slate-100 px-4 py-2 text-sm text-slate-700 hover:bg-slate-200">关闭</button>
              <button
                type="button"
                disabled={!canUpload || busy}
                onClick={() => void addText()}
                className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 shadow-md shadow-indigo-200 disabled:opacity-50 disabled:shadow-none"
              >
                {busy ? '保存中…' : '确认入库'}
              </button>
            </div>
          </div>
        ) : null}

        {tab === 'url' ? (
          <div>
            <div className="text-xs font-semibold text-slate-700 mb-1.5">网页链接 (URL)</div>
            <input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition-all"
              placeholder="https://example.com/wiki/..."
            />
            <div className="mt-4 flex justify-end gap-3">
              <button type="button" onClick={onClose} className="rounded-xl bg-slate-100 px-4 py-2 text-sm text-slate-700 hover:bg-slate-200">关闭</button>
              <button
                type="button"
                disabled={!canUrl || busy}
                onClick={() => void addUrl()}
                className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 shadow-md shadow-indigo-200 disabled:opacity-50 disabled:shadow-none"
              >
                {busy ? '抓取中…' : '抓取并入库'}
              </button>
            </div>
          </div>
        ) : null}

        {tab === 'search' ? (
          <div>
            <div className="flex gap-2">
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition-all"
                placeholder="输入关键词搜索..."
              />
              <button
                type="button"
                onClick={() => void doSearch(search)}
                className="rounded-xl bg-slate-100 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-200 hover:text-indigo-600 transition-colors"
              >
                搜索
              </button>
            </div>
            <div className="mt-4 space-y-3 max-h-[300px] overflow-auto pr-1 scrollbar-thin">
              {results.length === 0 ? (
                <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm text-slate-500">暂无相关资料</div>
              ) : (
                results.map((d) => (
                  <div key={d.id} className="rounded-xl border border-slate-200 bg-white p-4 hover:border-indigo-200 transition-colors shadow-sm">
                    <div className="text-sm font-bold text-slate-900">{d.title || '无标题'}</div>
                    <div className="mt-1 text-xs text-slate-500">{d.source}{d.source_uri ? ` · ${d.source_uri}` : ''}</div>
                    <div className="mt-2 p-2 bg-slate-50 rounded-lg text-xs text-slate-600 line-clamp-3 leading-relaxed">
                      {d.content}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        ) : null}
      </div>
    </Modal>
  )
}
