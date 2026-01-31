import { ArrowLeft, BookPlus, Save, Sparkles } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import MultiSelect from '@/components/MultiSelect'
import { api } from '@/utils/api'
import { useToastStore } from '@/stores/toastStore'

const GENRES = [
  '玄幻',
  '奇幻',
  '仙侠',
  '都市',
  '历史',
  '科幻',
  '悬疑',
  '言情',
  '轻小说',
  '灵异',
  '游戏',
].map((x) => ({ value: x, label: x }))

const STYLE_TAGS = ['爆爽', '热血', '轻松', '黑暗', '智斗', '甜宠', '群像', '升级流', '日常', '爽点密集'].map((x) => ({ value: x, label: x }))

const READERS = ['男频', '女频', '学生', '上班族', '轻度读者', '重度读者'].map((x) => ({ value: x, label: x }))

type CreateNovelResp = {
  id: string
  title: string
}

export default function NewNovel() {
  const nav = useNavigate()
  const toast = useToastStore((s) => s.push)
  const [loading, setLoading] = useState(false)

  const [title, setTitle] = useState('')
  const [genres, setGenres] = useState<string[]>([])
  const [tags, setTags] = useState<string[]>([])
  const [readers, setReaders] = useState<string[]>([])
  const [totalWords, setTotalWords] = useState(2000000)
  const [minChapterWords, setMinChapterWords] = useState(2500)
  const [background, setBackground] = useState('')

  const canSubmit = useMemo(() => background.trim().length > 10 && totalWords > 0 && minChapterWords > 0, [background, totalWords, minChapterWords])

  async function submit() {
    if (!canSubmit || loading) return
    setLoading(true)
    try {
      const res = await api<CreateNovelResp>('/api/novels', {
        method: 'POST',
        body: JSON.stringify({
          title: title.trim() || undefined,
          setting: {
            genres,
            style_tags: tags,
            target_readers: readers,
            total_words: totalWords,
            min_chapter_words: minChapterWords,
            background,
          },
        }),
      })
      toast({ level: 'success', title: '已创建小说', message: res.title })
      nav(`/novels/${res.id}`)
    } catch (e) {
      toast({ level: 'error', title: '创建失败', message: e instanceof Error ? e.message : String(e) })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-900 pb-10">
      <div className="mx-auto max-w-7xl px-5 py-8">
        <div className="flex items-center justify-between gap-4 mb-8">
          <button
            type="button"
            onClick={() => nav('/')}
            className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm border border-slate-200 hover:bg-slate-50 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            返回藏书阁
          </button>
          <div className="text-right">
            <div className="text-base font-bold text-slate-900">新建小说设定</div>
            <div className="text-xs text-slate-500">完善基础设定，后续 AI 将协助你完成创作</div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
          <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
            <h2 className="text-lg font-bold mb-6 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-indigo-500" />
              基础信息
            </h2>
            <div className="grid gap-6">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">小说名称（可选）</label>
                <input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 focus:border-indigo-500 focus:bg-white focus:ring-2 focus:ring-indigo-200 outline-none transition-all placeholder:text-slate-400"
                  placeholder="如：天道图书馆（留空则生成后自动命名）"
                />
              </div>

              <div className="grid gap-6 md:grid-cols-3">
                <MultiSelect label="小说类型" value={genres} onChange={setGenres} options={GENRES} placeholder="选择类型" />
                <MultiSelect label="风格标签" value={tags} onChange={setTags} options={STYLE_TAGS} placeholder="选择风格" />
                <MultiSelect label="目标读者" value={readers} onChange={setReaders} options={READERS} placeholder="选择读者" />
              </div>

              <div className="grid gap-6 md:grid-cols-2">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2">预计总字数</label>
                  <input
                    value={totalWords}
                    onChange={(e) => setTotalWords(Number(e.target.value || 0))}
                    type="number"
                    min={1}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 focus:border-indigo-500 focus:bg-white focus:ring-2 focus:ring-indigo-200 outline-none transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2">每章最少字数</label>
                  <input
                    value={minChapterWords}
                    onChange={(e) => setMinChapterWords(Number(e.target.value || 0))}
                    type="number"
                    min={1}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 focus:border-indigo-500 focus:bg-white focus:ring-2 focus:ring-indigo-200 outline-none transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">世界观与故事背景（核心必填）</label>
                <textarea
                  value={background}
                  onChange={(e) => setBackground(e.target.value)}
                  className="h-64 w-full resize-none rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 focus:border-indigo-500 focus:bg-white focus:ring-2 focus:ring-indigo-200 outline-none transition-all placeholder:text-slate-400 leading-relaxed"
                  placeholder="请详细描述世界观、核心矛盾、主角身份与目标、金手指设定、爽点来源等..."
                />
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-2 text-base font-bold text-slate-900 mb-4">
                <BookPlus className="h-5 w-5 text-indigo-500" />
                创作助手提示
              </div>
              <div className="space-y-3 text-sm text-slate-600 leading-relaxed">
                <p>🚀 设定越详细，AI 生成的内容越符合预期。</p>
                <p>📝 创建后将进入工作流，依次生成 <span className="font-semibold text-slate-900">大纲 → 书名 → 章节编排 → 正文</span>。</p>
                <p>⚙️ 默认内置了DeepSeek API密匙，可中途修改。</p>
              </div>
            </div>

            <button
              type="button"
              disabled={!canSubmit || loading}
              onClick={submit}
              className="w-full inline-flex items-center justify-center gap-2 rounded-2xl bg-indigo-600 px-6 py-4 text-base font-semibold text-white shadow-xl shadow-indigo-200 hover:bg-indigo-700 hover:-translate-y-0.5 transition-all disabled:cursor-not-allowed disabled:opacity-50 disabled:shadow-none disabled:hover:translate-y-0"
            >
              <Save className="h-5 w-5" />
              {loading ? '正在创建...' : '确认创建并进入工作流'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
