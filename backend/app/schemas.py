import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class NovelSettingIn(BaseModel):
  genres: list[str] = Field(default_factory=list)
  style_tags: list[str] = Field(default_factory=list)
  target_readers: list[str] = Field(default_factory=list)
  total_words: int
  min_chapter_words: int
  background: str


class NovelCreateIn(BaseModel):
  title: str | None = None
  setting: NovelSettingIn


class NovelSettingOut(NovelSettingIn):
  deepseek_key_configured: bool = False
  deepseek_key_updated_at: datetime | None = None
  deepseek_base_url: str | None = None
  deepseek_model: str | None = None


class NovelOut(BaseModel):
  id: uuid.UUID
  title: str
  created_at: datetime
  updated_at: datetime


class ChapterOut(BaseModel):
  id: uuid.UUID
  volume_no: int
  chapter_no: int
  title: str
  status: str
  outline: str | None = None
  fine_outline: str | None = None
  content: str | None = None


class OutlineOut(BaseModel):
  version: int
  content: str
  created_at: datetime


class TitleOut(BaseModel):
  version: int
  titles: list[str]
  selected_title: str | None
  created_at: datetime


class PlanOut(BaseModel):
  version: int
  plan: dict
  created_at: datetime


class NovelBibleOut(BaseModel):
  version: int
  content: str
  created_at: datetime


class NovelDetailOut(NovelOut):
  setting: NovelSettingOut
  latest_outline: OutlineOut | None
  latest_titles: TitleOut | None
  latest_plan: PlanOut | None
  latest_bible: NovelBibleOut | None = None
  chapters: list[ChapterOut]


class SaveOutlineIn(BaseModel):
  content: str


class SaveTitlesSelectionIn(BaseModel):
  selected_title: str


class UpdateDeepSeekKeyIn(BaseModel):
  api_key: str
  base_url: str | None = None
  model: str | None = None


class BatchChaptersRunIn(BaseModel):
  only_pending: bool = True
  limit: int | None = None


class RunOut(BaseModel):
  id: uuid.UUID
  novel_id: uuid.UUID
  kind: str
  status: str
  current_step: str | None
  error_message: str | None
  created_at: datetime
  updated_at: datetime


class RunEventOut(BaseModel):
  id: uuid.UUID
  run_id: uuid.UUID
  level: str
  agent: str
  type: str
  message: str
  payload: dict
  created_at: datetime


class KnowledgeDocIn(BaseModel):
  title: str | None = None
  content: str


class KnowledgeUrlIn(BaseModel):
  url: str
  title: str | None = None


class KnowledgeDocOut(BaseModel):
  id: uuid.UUID
  novel_id: uuid.UUID
  source: str
  source_uri: str | None
  title: str
  content: str
  created_at: datetime
  updated_at: datetime
