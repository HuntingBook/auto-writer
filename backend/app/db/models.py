import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
  pass


class RunStatus(str, enum.Enum):
  draft = "draft"
  running = "running"
  paused = "paused"
  canceled = "canceled"
  succeeded = "succeeded"
  failed = "failed"


class RunKind(str, enum.Enum):
  outline = "outline"
  titles = "titles"
  plan = "plan"
  chapter = "chapter"
  chapters = "chapters"


class Novel(Base):
  __tablename__ = "novels"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  title: Mapped[str] = mapped_column(String(255), nullable=False, default="未命名")
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
  updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class NovelSetting(Base):
  __tablename__ = "novel_settings"

  novel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
  genres: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
  style_tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
  target_readers: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
  total_words: Mapped[int] = mapped_column(Integer, nullable=False, default=1000000)
  min_chapter_words: Mapped[int] = mapped_column(Integer, nullable=False, default=2000)
  background: Mapped[str] = mapped_column(Text, nullable=False, default="")

  deepseek_key_configured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
  deepseek_key_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
  deepseek_base_url: Mapped[str | None] = mapped_column(Text, nullable=True)
  deepseek_model: Mapped[str | None] = mapped_column(Text, nullable=True)

  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
  updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class OutlineVersion(Base):
  __tablename__ = "outline_versions"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  novel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
  version: Mapped[int] = mapped_column(Integer, nullable=False)
  content: Mapped[str] = mapped_column(Text, nullable=False)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class TitleVersion(Base):
  __tablename__ = "title_versions"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  novel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
  version: Mapped[int] = mapped_column(Integer, nullable=False)
  titles: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
  selected_title: Mapped[str | None] = mapped_column(Text, nullable=True)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PlanVersion(Base):
  __tablename__ = "plan_versions"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  novel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
  version: Mapped[int] = mapped_column(Integer, nullable=False)
  plan: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ChapterStatus(str, enum.Enum):
  pending = "pending"
  generating = "generating"
  done = "done"
  failed = "failed"


class Chapter(Base):
  __tablename__ = "chapters"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  novel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
  volume_no: Mapped[int] = mapped_column(Integer, nullable=False)
  chapter_no: Mapped[int] = mapped_column(Integer, nullable=False)
  title: Mapped[str] = mapped_column(String(255), nullable=False)

  status: Mapped[ChapterStatus] = mapped_column(Enum(ChapterStatus), nullable=False, default=ChapterStatus.pending)
  outline: Mapped[str | None] = mapped_column(Text, nullable=True)
  fine_outline: Mapped[str | None] = mapped_column(Text, nullable=True)
  content: Mapped[str | None] = mapped_column(Text, nullable=True)

  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
  updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Run(Base):
  __tablename__ = "runs"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  novel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
  kind: Mapped[RunKind] = mapped_column(Enum(RunKind), nullable=False)
  status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), nullable=False, default=RunStatus.draft)
  current_step: Mapped[str | None] = mapped_column(Text, nullable=True)
  error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
  updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class RunEventLevel(str, enum.Enum):
  info = "info"
  warn = "warn"
  error = "error"


class RunEvent(Base):
  __tablename__ = "run_events"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("runs.id"), index=True, nullable=False)
  level: Mapped[RunEventLevel] = mapped_column(Enum(RunEventLevel), nullable=False, default=RunEventLevel.info)
  agent: Mapped[str] = mapped_column(Text, nullable=False, default="orchestrator")
  type: Mapped[str] = mapped_column(Text, nullable=False)
  message: Mapped[str] = mapped_column(Text, nullable=False)
  payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class NovelBibleVersion(Base):
  __tablename__ = "novel_bible_versions"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  novel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
  version: Mapped[int] = mapped_column(Integer, nullable=False)
  content: Mapped[str] = mapped_column(Text, nullable=False)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class KnowledgeDocSource(str, enum.Enum):
  upload = "upload"
  url = "url"
  note = "note"


class KnowledgeDoc(Base):
  __tablename__ = "knowledge_docs"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  novel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
  source: Mapped[KnowledgeDocSource] = mapped_column(Enum(KnowledgeDocSource), nullable=False, default=KnowledgeDocSource.upload)
  source_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
  title: Mapped[str] = mapped_column(Text, nullable=False, default="")
  content: Mapped[str] = mapped_column(Text, nullable=False, default="")
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
  updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class KnowledgeEmbedding(Base):
  __tablename__ = "knowledge_embeddings"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  doc_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_docs.id"), index=True, nullable=False)
  model: Mapped[str] = mapped_column(Text, nullable=False, default="deepseek-embedding-v2")
  dims: Mapped[int] = mapped_column(Integer, nullable=False, default=768)
  embedding: Mapped[object] = mapped_column(Vector(768), nullable=False)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
