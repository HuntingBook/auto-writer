export function runKindLabel(kind: string): string {
  switch (kind) {
    case 'outline':
      return '大纲'
    case 'titles':
      return '书名'
    case 'plan':
      return '编排'
    case 'chapter':
      return '单章'
    case 'chapters':
      return '批量'
    default:
      return kind
  }
}

export function runStatusLabel(status: string): string {
  switch (status) {
    case 'draft':
      return '待运行'
    case 'running':
      return '运行中'
    case 'paused':
      return '已暂停'
    case 'succeeded':
      return '已完成'
    case 'failed':
      return '失败'
    case 'canceled':
      return '已取消'
    default:
      return status
  }
}

export function eventTypeLabel(type: string): string {
  switch (type) {
    case 'RUN_CREATED':
      return '已创建'
    case 'RUN_STARTED':
      return '运行开始'
    case 'RUN_SUCCEEDED':
      return '运行成功'
    case 'RUN_FAILED':
      return '运行失败'
    case 'RUN_CANCELED':
      return '已取消'
    case 'RUN_PAUSED':
      return '已暂停'
    case 'RUN_RESUMED':
      return '已继续'
    case 'STEP_STARTED':
      return '步骤开始'
    case 'STEP_OUTPUT':
      return '步骤输出'
    case 'STEP_FAILED':
      return '步骤失败'
    case 'STEP_WARN':
      return '步骤警告'
    default:
      return type
  }
}

export function agentLabel(agent: string): string {
  switch (agent) {
    case 'orchestrator':
      return '流程编排'
    case 'outline_agent':
      return '大纲助手'
    case 'bible_agent':
      return '设定助手'
    case 'title_agent':
      return '标题助手'
    case 'plan_agent':
      return '分卷助手'
    case 'chapter_outline_agent':
      return '章节大纲'
    case 'fine_outline_agent':
      return '细纲助手'
    case 'chapter_writer':
      return '正文写作'
    default:
      return agent
  }
}
