import { BookOpen, Wand2, Save, Check, Pencil, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { cn } from '@/lib/utils'
import type { NovelDetail, PlanVolume } from '@/types/novel'

type Step = 'outline' | 'titles' | 'plan' | 'chapter' | 'reader'

function StepTab({ active, label, onClick }: { active: boolean; label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'rounded-xl px-4 py-2 text-sm font-medium transition-all duration-200',
        active
          ? 'bg-indigo-50 text-indigo-700 shadow-sm ring-1 ring-indigo-200'
          : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
      )}
    >
      {label}
    </button>
  )
}

function SimpleMarkdown({ text }: { text: string }) {
  if (!text) return null

  const lines = text.split('\n')
  return (
    <div className="space-y-1 leading-relaxed">
      {lines.map((line, i) => {
        let content = line
        let type = 'p'
        let extraClass = ''

        if (line.startsWith('# ')) {
          content = line.slice(2)
          type = 'h1'
          extraClass = 'text-lg font-bold text-slate-900 mt-4 mb-2'
        } else if (line.startsWith('## ')) {
          content = line.slice(3)
          type = 'h2'
          extraClass = 'text-base font-bold text-slate-800 mt-3 mb-1.5'
        } else if (line.startsWith('### ')) {
          content = line.slice(4)
          type = 'h3'
          extraClass = 'text-sm font-bold text-slate-800 mt-2 mb-1'
        } else if (line.startsWith('- ') || line.startsWith('* ')) {
          content = line.slice(2)
          type = 'li'
          extraClass = 'list-disc list-inside pl-2'
        }

        // Parse bold
        const parts = content.split(/(\*\*.*?\*\*)/g)
        const children = parts.map((part, idx) => {
          if (part.startsWith('**') && part.endsWith('**')) {
            return <strong key={idx} className="font-semibold text-slate-900">{part.slice(2, -2)}</strong>
          }
          return <span key={idx}>{part}</span>
        })

        if (type === 'h1' || type === 'h2' || type === 'h3') return <div key={i} className={extraClass}>{children}</div>
        if (type === 'li') return <div key={i} className={cn("flex gap-2", extraClass)}><span className="text-slate-400">•</span><div>{children}</div></div>

        return <div key={i} className={cn("min-h-[1em]", extraClass)}>{children}</div>
      })}
    </div>
  )
}

type Props = {
  detail: NovelDetail
  activeStep: Step
  setActiveStep: (s: Step) => void
  outlineDraft: string
  setOutlineDraft: (v: string) => void
  onStartRun: (kind: 'outline' | 'titles' | 'plan') => void
  onSaveOutline: () => void
  onSaveSelectedTitle: (t: string) => void
  onStartChapterRun: (chapterId: string) => void
  onStartChaptersBatchRun: () => void
}

export default function WorkflowSteps({
  detail,
  activeStep,
  setActiveStep,
  outlineDraft,
  setOutlineDraft,
  onStartRun,
  onSaveOutline,
  onSaveSelectedTitle,
  onStartChapterRun,
  onStartChaptersBatchRun,
}: Props) {
  const volumes = useMemo<PlanVolume[]>(() => detail.latest_plan?.plan?.volumes || [], [detail.latest_plan])
  const [readingId, setReadingId] = useState<string | null>(detail.chapters[0]?.id || null)
  const reading = useMemo(() => detail.chapters.find((c) => c.id === readingId) || null, [detail.chapters, readingId])

  const [editingTitle, setEditingTitle] = useState(false)
  const [titleInput, setTitleInput] = useState('')

  function startEditTitle() {
    setTitleInput(detail.latest_titles?.selected_title || '')
    setEditingTitle(true)
  }

  function saveEditTitle() {
    if (titleInput.trim()) {
      onSaveSelectedTitle(titleInput.trim())
    }
    setEditingTitle(false)
  }

  return (
    <div className="rounded-3xl border border-slate-200 bg-white shadow-sm overflow-hidden flex flex-col min-h-[600px]">
      <div className="border-b border-slate-100 bg-slate-50/50 px-6 py-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-indigo-100 rounded-lg text-indigo-600">
              <BookOpen className="h-4 w-4" />
            </div>
            <div className="text-base font-bold text-slate-900">创作工作流</div>
          </div>
          <div className="flex flex-wrap gap-1 p-1 bg-slate-100/50 rounded-2xl border border-slate-200/50">
            <StepTab active={activeStep === 'outline'} label="大纲策划" onClick={() => setActiveStep('outline')} />
            <StepTab active={activeStep === 'titles'} label="书名生成" onClick={() => setActiveStep('titles')} />
            <StepTab active={activeStep === 'plan'} label="章节编排" onClick={() => setActiveStep('plan')} />
            <StepTab active={activeStep === 'chapter'} label="正文生成" onClick={() => setActiveStep('chapter')} />
            <StepTab active={activeStep === 'reader'} label="沉浸阅读" onClick={() => setActiveStep('reader')} />
          </div>
        </div>
      </div>

      <div className="flex-1 p-6">
        {activeStep === 'outline' ? (
          <div className="h-full flex flex-col">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
              <div className="text-sm text-slate-500 font-medium">版本：{detail.latest_outline?.version ? `v${detail.latest_outline.version}` : '无'}</div>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => onStartRun('outline')}
                  className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-md shadow-indigo-200 hover:bg-indigo-700 hover:-translate-y-0.5 transition-all"
                >
                  <Wand2 className="h-4 w-4" />
                  智能生成大纲
                </button>
                <button
                  type="button"
                  onClick={onSaveOutline}
                  className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm border border-slate-200 hover:bg-slate-50 transition-colors"
                >
                  <Save className="h-4 w-4" />
                  保存为新版本
                </button>
              </div>
            </div>
            <textarea
              value={outlineDraft}
              onChange={(e) => setOutlineDraft(e.target.value)}
              className="flex-1 w-full min-h-[500px] resize-none rounded-2xl border border-slate-200 bg-slate-50 p-6 text-sm text-slate-900 leading-relaxed focus:border-indigo-500 focus:bg-white focus:ring-2 focus:ring-indigo-100 outline-none transition-all"
              placeholder="此处将显示 AI 生成的大纲。你也可以手动编辑，完善后点击“保存为新版本”..."
            />
          </div>
        ) : null}

        {activeStep === 'titles' ? (
          <div>
            <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
              <div className="text-sm text-slate-500 font-medium">版本：{detail.latest_titles?.version ? `v${detail.latest_titles.version}` : '无'}</div>
              <button
                type="button"
                onClick={() => onStartRun('titles')}
                className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-md shadow-indigo-200 hover:bg-indigo-700 hover:-translate-y-0.5 transition-all"
              >
                <Wand2 className="h-4 w-4" />
                生成书名创意
              </button>
            </div>

            <div className="mb-6 rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50 to-white p-6 shadow-sm">
              <div className="text-xs font-semibold text-indigo-500 uppercase tracking-wider mb-2">当前已选书名</div>
              {editingTitle ? (
                <div className="flex items-center gap-2">
                  <input
                    value={titleInput}
                    onChange={(e) => setTitleInput(e.target.value)}
                    className="flex-1 rounded-xl border border-indigo-200 bg-white px-3 py-2 text-lg font-bold text-slate-900 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none"
                    placeholder="输入书名..."
                    autoFocus
                  />
                  <button
                    onClick={saveEditTitle}
                    className="p-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition-colors"
                  >
                    <Check className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => setEditingTitle(false)}
                    className="p-2 rounded-lg bg-white text-slate-500 border border-slate-200 hover:bg-slate-50 transition-colors"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
              ) : (
                <div className="flex items-center justify-between group">
                  <div className="text-2xl font-bold text-slate-900 tracking-tight">{detail.latest_titles?.selected_title || '尚未选择'}</div>
                  <button
                    onClick={startEditTitle}
                    className="p-2 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors opacity-0 group-hover:opacity-100"
                    title="编辑书名"
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                </div>
              )}
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {(detail.latest_titles?.titles || []).map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => onSaveSelectedTitle(t)}
                  className={cn(
                    'group relative rounded-2xl border p-5 text-left transition-all hover:shadow-md hover:-translate-y-0.5',
                    detail.latest_titles?.selected_title === t
                      ? 'border-indigo-500 bg-indigo-50 ring-1 ring-indigo-500'
                      : 'border-slate-200 bg-white hover:border-indigo-300'
                  )}
                >
                  <div className="flex justify-between items-start">
                    <div className="font-bold text-slate-900 group-hover:text-indigo-700 transition-colors">{t}</div>
                    {detail.latest_titles?.selected_title === t && (
                      <Check className="h-4 w-4 text-indigo-600" />
                    )}
                  </div>
                  <div className="mt-2 text-xs text-slate-500 group-hover:text-indigo-500">点击设为封面标题</div>
                </button>
              ))}
            </div>
          </div>
        ) : null}

        {activeStep === 'plan' ? (
          <div>
            <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
              <div className="text-sm text-slate-500 font-medium">版本：{detail.latest_plan?.version ? `v${detail.latest_plan.version}` : '无'}</div>
              <button
                type="button"
                onClick={() => onStartRun('plan')}
                className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-md shadow-indigo-200 hover:bg-indigo-700 hover:-translate-y-0.5 transition-all"
              >
                <Wand2 className="h-4 w-4" />
                生成分卷与章节编排
              </button>
            </div>

            {volumes.length > 0 ? (
              <div className="space-y-6">
                {volumes.map((v) => (
                  <div key={String(v.volume_no)} className="rounded-3xl border border-slate-200 bg-slate-50/50 p-5">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="h-8 w-1 bg-indigo-500 rounded-full"></div>
                      <div className="text-lg font-bold text-slate-900">第{v.volume_no}卷 · {v.volume_title || '未命名分卷'}</div>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                      {(v.chapters || []).map((c) => (
                        <div key={String(c.chapter_no)} className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm hover:border-indigo-200 hover:shadow-md transition-all">
                          <div className="text-xs font-medium text-slate-500 mb-1">第{c.chapter_no}章</div>
                          <div className="font-semibold text-slate-900">{c.title}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-12 text-center">
                <div className="text-slate-500">暂无编排内容。请先完成大纲，再生成章节结构。</div>
              </div>
            )}
          </div>
        ) : null}

        {activeStep === 'chapter' ? (
          <div>
            <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
              <div className="text-sm text-slate-500 font-medium">章节生成控制台</div>
              <button
                type="button"
                onClick={onStartChaptersBatchRun}
                className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm border border-slate-200 hover:bg-slate-50 hover:text-indigo-600 transition-all"
              >
                <Wand2 className="h-4 w-4" />
                批量自动生成（轮询）
              </button>
            </div>
            <div className="space-y-3">
              {detail.chapters.map((c) => (
                <div key={c.id} className="group flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-4 transition-all hover:shadow-md hover:border-indigo-200">
                  <div className="min-w-0 flex items-center gap-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-bold text-slate-600 group-hover:bg-indigo-50 group-hover:text-indigo-600">
                      {c.chapter_no}
                    </div>
                    <div>
                      <div className="text-xs text-slate-500">第{c.volume_no}卷</div>
                      <div className="truncate text-base font-bold text-slate-900">{c.title}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={cn(
                      'rounded-full px-2.5 py-1 text-xs font-medium',
                      c.status === 'done' && 'bg-emerald-50 text-emerald-700 border border-emerald-100',
                      c.status === 'pending' && 'bg-slate-100 text-slate-700 border border-slate-200',
                      c.status === 'generating' && 'bg-blue-50 text-blue-700 border border-blue-100',
                      c.status === 'failed' && 'bg-red-50 text-red-700 border border-red-100'
                    )}>
                      {c.status === 'done' ? '已完成' : c.status === 'pending' ? '待生成' : c.status === 'generating' ? '生成中' : c.status === 'failed' ? '失败' : c.status}
                    </span>
                    <button
                      type="button"
                      onClick={() => onStartChapterRun(c.id)}
                      className="inline-flex items-center gap-2 rounded-xl bg-indigo-50 px-3 py-2 text-sm font-medium text-indigo-700 hover:bg-indigo-100 transition-colors"
                    >
                      <Wand2 className="h-4 w-4" />
                      生成
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {activeStep === 'reader' ? (
          <div className="h-full grid gap-6 lg:grid-cols-[280px_1fr]">
            <div className="rounded-3xl border border-slate-200 bg-white shadow-sm overflow-hidden flex flex-col">
              <div className="bg-slate-50 p-3 border-b border-slate-100 text-xs font-bold text-slate-500 uppercase tracking-wider">目录</div>
              <div className="flex-1 overflow-auto p-2 scrollbar-thin">
                {detail.chapters.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => setReadingId(c.id)}
                    className={cn(
                      'w-full rounded-xl px-4 py-3 text-left mb-1 transition-all',
                      readingId === c.id
                        ? 'bg-indigo-50 text-indigo-900 shadow-sm ring-1 ring-indigo-200'
                        : 'text-slate-700 hover:bg-slate-50'
                    )}
                  >
                    <div className="text-xs text-opacity-70 mb-0.5">第{c.volume_no}卷 · 第{c.chapter_no}章</div>
                    <div className="truncate font-semibold">{c.title}</div>
                  </button>
                ))}
              </div>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm overflow-auto max-h-[700px]">
              {!reading ? (
                <div className="flex h-full items-center justify-center text-slate-400">选择章节开始阅读</div>
              ) : (
                <div className="max-w-3xl mx-auto">
                  <div className="text-center mb-8">
                    <div className="text-sm font-medium text-slate-500 uppercase tracking-widest mb-2">第{reading.volume_no}卷 · 第{reading.chapter_no}章</div>
                    <h2 className="text-2xl font-bold text-slate-900">{reading.title}</h2>
                  </div>

                  <div className="prose prose-slate prose-lg mx-auto">
                    {reading.content ? (
                      <div className="whitespace-pre-wrap leading-loose text-justify text-slate-800 font-serif">
                        {reading.content}
                      </div>
                    ) : (
                      <div className="rounded-2xl bg-slate-50 p-8 text-center text-slate-500 border border-dashed border-slate-200">
                        本章正文尚未生成，请前往“正文生成”步骤处理。
                      </div>
                    )}

                    {reading.outline && (
                      <div className="mt-12 pt-8 border-t border-slate-100">
                        <div className="text-xs font-bold text-slate-400 uppercase mb-4">本章大纲摘要</div>
                        <div className="rounded-2xl bg-slate-50 p-6 text-sm text-slate-600 leading-relaxed">
                          <SimpleMarkdown text={reading.outline} />
                        </div>
                      </div>
                    )}

                    {reading.fine_outline && (
                      <div className="mt-8 pt-8 border-t border-slate-100">
                        <div className="text-xs font-bold text-slate-400 uppercase mb-4">本章细纲（场景/节拍）</div>
                        <div className="rounded-2xl bg-slate-50 p-6 text-sm text-slate-600 leading-relaxed">
                          <SimpleMarkdown text={reading.fine_outline} />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}
