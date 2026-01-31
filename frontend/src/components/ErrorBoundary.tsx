import React from 'react'
import { useToastStore } from '@/stores/toastStore'

type Props = {
  children: React.ReactNode
}

type State = {
  hasError: boolean
}

export default class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  componentDidCatch(error: unknown) {
    useToastStore.getState().push({ level: 'error', title: '页面出错', message: error instanceof Error ? error.message : String(error) })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-zinc-50 px-6 text-center text-zinc-900">
          <div className="max-w-md rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
            <div className="text-base font-semibold">页面出错</div>
            <div className="mt-2 text-sm text-zinc-600">请刷新重试，或返回首页重新进入。</div>
            <div className="mt-4 flex justify-center gap-2">
              <a href="/" className="rounded-lg bg-zinc-100 px-3 py-2 text-sm text-zinc-900 hover:bg-zinc-200">回到首页</a>
              <button
                type="button"
                onClick={() => window.location.reload()}
                className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-500"
              >
                刷新
              </button>
            </div>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
