"""init

Revision ID: 0001_init
Revises:
Create Date: 2026-01-31

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
  op.create_table(
    "novels",
    sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
    sa.Column("title", sa.String(length=255), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
  )
  op.create_index("ix_novels_updated_at", "novels", ["updated_at"], unique=False)

  op.create_table(
    "novel_settings",
    sa.Column("novel_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
    sa.Column("genres", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
    sa.Column("style_tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
    sa.Column("target_readers", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
    sa.Column("total_words", sa.Integer(), nullable=False, server_default="1000000"),
    sa.Column("min_chapter_words", sa.Integer(), nullable=False, server_default="2000"),
    sa.Column("background", sa.Text(), nullable=False, server_default=""),
    sa.Column("deepseek_key_encrypted", sa.Text(), nullable=True),
    sa.Column("deepseek_base_url", sa.Text(), nullable=True),
    sa.Column("deepseek_model", sa.Text(), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
  )

  op.create_table(
    "outline_versions",
    sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
    sa.Column("novel_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("version", sa.Integer(), nullable=False),
    sa.Column("content", sa.Text(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
  )
  op.create_index("ix_outline_versions_novel_id", "outline_versions", ["novel_id"], unique=False)

  op.create_table(
    "title_versions",
    sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
    sa.Column("novel_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("version", sa.Integer(), nullable=False),
    sa.Column("titles", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
    sa.Column("selected_title", sa.Text(), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
  )
  op.create_index("ix_title_versions_novel_id", "title_versions", ["novel_id"], unique=False)

  op.create_table(
    "plan_versions",
    sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
    sa.Column("novel_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("version", sa.Integer(), nullable=False),
    sa.Column("plan", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
  )
  op.create_index("ix_plan_versions_novel_id", "plan_versions", ["novel_id"], unique=False)

  op.create_table(
    "chapters",
    sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
    sa.Column("novel_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("volume_no", sa.Integer(), nullable=False),
    sa.Column("chapter_no", sa.Integer(), nullable=False),
    sa.Column("title", sa.String(length=255), nullable=False),
    sa.Column("status", sa.Enum("pending", "generating", "done", "failed", name="chapterstatus"), nullable=False, server_default="pending"),
    sa.Column("outline", sa.Text(), nullable=True),
    sa.Column("content", sa.Text(), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
  )
  op.create_index("ix_chapters_novel_id", "chapters", ["novel_id"], unique=False)

  op.create_table(
    "runs",
    sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
    sa.Column("novel_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("kind", sa.Enum("outline", "titles", "plan", "chapter", name="runkind"), nullable=False),
    sa.Column("status", sa.Enum("draft", "running", "paused", "canceled", "succeeded", "failed", name="runstatus"), nullable=False, server_default="draft"),
    sa.Column("current_step", sa.Text(), nullable=True),
    sa.Column("error_message", sa.Text(), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
  )
  op.create_index("ix_runs_novel_id", "runs", ["novel_id"], unique=False)

  op.create_table(
    "run_events",
    sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
    sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("runs.id"), nullable=False),
    sa.Column("level", sa.Enum("info", "warn", "error", name="runeventlevel"), nullable=False, server_default="info"),
    sa.Column("agent", sa.Text(), nullable=False, server_default="orchestrator"),
    sa.Column("type", sa.Text(), nullable=False),
    sa.Column("message", sa.Text(), nullable=False),
    sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
  )
  op.create_index("ix_run_events_run_id", "run_events", ["run_id"], unique=False)


def downgrade() -> None:
  op.drop_index("ix_run_events_run_id", table_name="run_events")
  op.drop_table("run_events")
  op.execute("DROP TYPE runeventlevel")
  op.drop_index("ix_runs_novel_id", table_name="runs")
  op.drop_table("runs")
  op.execute("DROP TYPE runkind")
  op.execute("DROP TYPE runstatus")
  op.drop_index("ix_chapters_novel_id", table_name="chapters")
  op.drop_table("chapters")
  op.execute("DROP TYPE chapterstatus")
  op.drop_index("ix_plan_versions_novel_id", table_name="plan_versions")
  op.drop_table("plan_versions")
  op.drop_index("ix_title_versions_novel_id", table_name="title_versions")
  op.drop_table("title_versions")
  op.drop_index("ix_outline_versions_novel_id", table_name="outline_versions")
  op.drop_table("outline_versions")
  op.drop_table("novel_settings")
  op.drop_index("ix_novels_updated_at", table_name="novels")
  op.drop_table("novels")
