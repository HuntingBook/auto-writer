export type Chapter = {
  id: string
  volume_no: number
  chapter_no: number
  title: string
  status: string
  outline?: string | null
  fine_outline?: string | null
  content?: string | null
}

export type PlanChapter = {
  chapter_no: number
  title: string
}

export type PlanVolume = {
  volume_no: number
  volume_title?: string
  chapters: PlanChapter[]
}

export type Plan = {
  volumes: PlanVolume[]
}

export type NovelDetail = {
  id: string
  title: string
  setting: {
    genres: string[]
    style_tags: string[]
    target_readers: string[]
    total_words: number
    min_chapter_words: number
    background: string
    deepseek_key_configured?: boolean
    deepseek_key_updated_at?: string | null
    deepseek_base_url?: string | null
    deepseek_model?: string | null
  }
  latest_outline?: { version: number; content: string; created_at: string } | null
  latest_titles?: { version: number; titles: string[]; selected_title?: string | null; created_at: string } | null
  latest_plan?: { version: number; plan: Plan; created_at: string } | null
  latest_bible?: { version: number; content: string; created_at: string } | null
  chapters: Chapter[]
}

export type Run = {
  id: string
  kind: string
  status: string
  current_step?: string | null
  error_message?: string | null
}
