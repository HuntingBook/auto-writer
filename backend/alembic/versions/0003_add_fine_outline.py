"""add_fine_outline

Revision ID: 0003_add_fine_outline
Revises: 0002_kb_and_key_storage
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_add_fine_outline"
down_revision = "0002_kb_and_key_storage"
branch_labels = None
depends_on = None


def upgrade() -> None:
  op.add_column("chapters", sa.Column("fine_outline", sa.Text(), nullable=True))


def downgrade() -> None:
  op.drop_column("chapters", "fine_outline")
