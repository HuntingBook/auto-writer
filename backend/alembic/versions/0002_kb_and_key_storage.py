"""kb_and_key_storage

Revision ID: 0002_kb_and_key_storage
Revises: 0001_init
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from pgvector.sqlalchemy import Vector


revision = "0002_kb_and_key_storage"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
  op.execute("CREATE EXTENSION IF NOT EXISTS vector")

  op.add_column(
    "novel_settings",
    sa.Column("deepseek_key_configured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
  )
  op.add_column(
    "novel_settings",
    sa.Column("deepseek_key_updated_at", sa.DateTime(timezone=True), nullable=True),
  )
  op.drop_column("novel_settings", "deepseek_key_encrypted")

  op.execute("ALTER TYPE runkind ADD VALUE IF NOT EXISTS 'chapters'")

  op.create_table(
    "novel_bible_versions",
    sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
    sa.Column("novel_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("version", sa.Integer(), nullable=False),
    sa.Column("content", sa.Text(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
  )
  op.create_index("ix_novel_bible_versions_novel_id", "novel_bible_versions", ["novel_id"], unique=False)

  op.create_table(
    "knowledge_docs",
    sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
    sa.Column("novel_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("source", sa.Enum("upload", "url", "note", name="knowledgedocsource"), nullable=False, server_default="upload"),
    sa.Column("source_uri", sa.Text(), nullable=True),
    sa.Column("title", sa.Text(), nullable=False, server_default=""),
    sa.Column("content", sa.Text(), nullable=False, server_default=""),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
  )
  op.create_index("ix_knowledge_docs_novel_id", "knowledge_docs", ["novel_id"], unique=False)

  op.create_table(
    "knowledge_embeddings",
    sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
    sa.Column("doc_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_docs.id"), nullable=False),
    sa.Column("model", sa.Text(), nullable=False, server_default="deepseek-embedding-v2"),
    sa.Column("dims", sa.Integer(), nullable=False, server_default="768"),
    sa.Column("embedding", Vector(768), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
  )
  op.create_index("ix_knowledge_embeddings_doc_id", "knowledge_embeddings", ["doc_id"], unique=False)


def downgrade() -> None:
  op.drop_index("ix_knowledge_embeddings_doc_id", table_name="knowledge_embeddings")
  op.drop_table("knowledge_embeddings")
  op.drop_index("ix_knowledge_docs_novel_id", table_name="knowledge_docs")
  op.drop_table("knowledge_docs")
  op.execute("DROP TYPE knowledgedocsource")

  op.drop_index("ix_novel_bible_versions_novel_id", table_name="novel_bible_versions")
  op.drop_table("novel_bible_versions")

  op.add_column("novel_settings", sa.Column("deepseek_key_encrypted", sa.Text(), nullable=True))
  op.drop_column("novel_settings", "deepseek_key_updated_at")
  op.drop_column("novel_settings", "deepseek_key_configured")
