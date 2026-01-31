import Modal from '@/components/Modal'

type Props = {
  open: boolean
  onClose: () => void
  apiKey: string
  setApiKey: (v: string) => void
  baseUrl: string
  setBaseUrl: (v: string) => void
  model: string
  setModel: (v: string) => void
  onSave: () => Promise<void>
}

export default function DeepSeekModal({
  open,
  onClose,
  apiKey,
  setApiKey,
  baseUrl,
  setBaseUrl,
  model,
  setModel,
  onSave,
}: Props) {
  return (
    <Modal title="DeepSeek 模型配置" open={open} onClose={onClose}>
      <div className="space-y-4">
        <div>
          <div className="text-xs font-semibold text-slate-700 mb-1.5">API Key (密钥)</div>
          <input
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition-all"
            placeholder="请输入以 sk- 开头的密钥"
            type="password"
          />
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <div className="text-xs font-semibold text-slate-700 mb-1.5">API Base URL (地址)</div>
            <input
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition-all"
            />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-700 mb-1.5">Model Name (模型)</div>
            <input
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition-all"
            />
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl bg-slate-100 px-4 py-2 text-sm text-slate-700 hover:bg-slate-200 transition-colors"
          >
            取消
          </button>
          <button
            type="button"
            onClick={() => void onSave()}
            className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 shadow-md shadow-indigo-200 transition-all"
          >
            保存配置
          </button>
        </div>

        <div className="rounded-xl border border-blue-100 bg-blue-50 p-4 text-xs text-blue-800 leading-relaxed">
          安全提示：您的密钥仅用于当前浏览器会话进行 API 调用，不会永久存储在服务器数据库中。
        </div>
      </div>
    </Modal>
  )
}
