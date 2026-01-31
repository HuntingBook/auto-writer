import { BookPlus, LibraryBig, RefreshCw, Trash2 } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '@/utils/api'
import { useToastStore } from '@/stores/toastStore'

type Novel = {
  id: string
  title: string
  updated_at: string
}

import Modal from '@/components/Modal'

export default function Home() {
  const nav = useNavigate()
  const toast = useToastStore((s) => s.push)
  const [items, setItems] = useState<Novel[]>([])
  const [loading, setLoading] = useState(true)

  const [deleteId, setDeleteId] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api<Novel[]>('/api/novels')
      setItems(res)
    } catch (e) {
      toast({ level: 'error', title: '加载失败', message: e instanceof Error ? e.message : String(e) })
    } finally {
      setLoading(false)
    }
  }, [toast])

  async function confirmDelete() {
    if (!deleteId) return
    try {
      await api(`/api/novels/${deleteId}`, { method: 'DELETE' })
      toast({ level: 'success', title: '已删除' })
      setDeleteId(null)
      await refresh()
    } catch (e) {
      toast({ level: 'error', title: '删除失败', message: e instanceof Error ? e.message : String(e) })
    }
  }

  function openDeleteModal(e: React.MouseEvent, id: string) {
    e.stopPropagation()
    setDeleteId(id)
  }

  useEffect(() => {
    refresh()
  }, [refresh])

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-900 pb-10">
      <div className="mx-auto max-w-7xl px-5 py-8">
        <div className="flex flex-wrap items-end justify-between gap-3 mb-8">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-600 rounded-lg shadow-lg shadow-indigo-200">
                <LibraryBig className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900">智作 · 藏书阁</h1>
            </div>
            <div className="mt-2 text-sm text-slate-500 font-medium">
              全自动网文创作助手：大纲策划 · 书名生成 · 章节编排 · 沉浸阅读
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={refresh}
              className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm border border-slate-200 hover:bg-slate-50 transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
              刷新
            </button>
            <button
              type="button"
              onClick={() => nav('/novels/new')}
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-lg shadow-indigo-200 hover:bg-indigo-700 transition-all hover:-translate-y-0.5"
            >
              <BookPlus className="h-4 w-4" />
              新建小说
            </button>
          </div>
        </div>

        <div className="mt-6">
          {loading ? (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="h-48 animate-pulse rounded-3xl bg-white border border-slate-100 shadow-sm" />
              ))}
            </div>
          ) : items.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-20 text-center">
              <div className="p-4 bg-white rounded-full shadow-sm mb-4">
                <LibraryBig className="h-8 w-8 text-slate-400" />
              </div>
              <div className="text-base font-semibold text-slate-900">你的藏书阁还是空的</div>
              <div className="mt-2 text-sm text-slate-500 max-w-xs mx-auto">
                创建一个新的小说设定，AI 将协助你完成从大纲到正文的全流程创作。
              </div>
              <button
                type="button"
                onClick={() => nav('/novels/new')}
                className="mt-6 inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white shadow-lg shadow-indigo-200 hover:bg-indigo-700 transition-all"
              >
                <BookPlus className="h-4 w-4" />
                立即创建
              </button>
            </div>
          ) : (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {items.map((n) => (
                <div
                  key={n.id}
                  onClick={() => nav(`/novels/${n.id}`)}
                  className="group relative flex flex-col justify-between overflow-hidden rounded-3xl border border-slate-200 bg-white p-5 text-left shadow-sm transition-all hover:shadow-xl hover:border-indigo-100 hover:-translate-y-1 cursor-pointer"
                >
                  <div className="absolute top-0 right-0 h-24 w-24 translate-x-8 translate-y-[-2rem] rounded-full bg-gradient-to-br from-indigo-50 to-purple-50 blur-2xl group-hover:from-indigo-100 group-hover:to-purple-100 transition-colors" />

                  <div className="relative z-10">
                    <div className="flex justify-between items-start">
                      <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 font-bold text-xl group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                        {n.title.slice(0, 1)}
                      </div>
                      <button
                        type="button"
                        onClick={(e) => openDeleteModal(e, n.id)}
                        className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-colors"
                        title="删除小说"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>

                    <div className="line-clamp-2 text-lg font-bold text-slate-900 group-hover:text-indigo-700 transition-colors">
                      {n.title}
                    </div>
                  </div>

                  <div className="relative z-10 mt-6 flex items-center justify-between border-t border-slate-100 pt-4">
                    <div className="text-xs font-medium text-slate-400">
                      {new Date(n.updated_at).toLocaleDateString('zh-CN')}
                    </div>
                    <div className="text-xs font-bold text-indigo-600 opacity-0 transform translate-x-2 transition-all group-hover:opacity-100 group-hover:translate-x-0">
                      进入创作 →
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>


        <Modal open={!!deleteId} onClose={() => setDeleteId(null)} title="确认操作">
          <div className="space-y-4">
            <div className="text-sm text-slate-600 leading-relaxed">
              确定要删除这部小说吗？此操作无法撤销，所有相关的大纲、章节和生成记录都将被永久删除。
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setDeleteId(null)}
                className="rounded-xl bg-slate-100 px-4 py-2 text-sm text-slate-700 hover:bg-slate-200 transition-colors"
              >
                取消
              </button>
              <button
                type="button"
                onClick={() => void confirmDelete()}
                className="rounded-xl bg-red-600 px-4 py-2 text-sm font-medium text-white shadow-md shadow-red-200 hover:bg-red-700 transition-all"
              >
                确认删除
              </button>
            </div>
          </div>
        </Modal>
      </div>
    </div>
  )
}
