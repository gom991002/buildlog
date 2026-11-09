"""create materials table

Revision ID: c3e8f1a7b2d4
Revises: a12cf3d224b6
Create Date: 2026-10-27 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3e8f1a7b2d4'
down_revision: Union[str, Sequence[str], None] = 'a12cf3d224b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('materials',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('memo', sa.String(length=1000), nullable=True),
    sa.Column('original_filename', sa.String(length=255), nullable=False),
    sa.Column('stored_filename', sa.String(length=64), nullable=False),
    sa.Column('content_type', sa.String(length=20), nullable=False),
    sa.Column('file_size', sa.Integer(), nullable=False),
    sa.Column('ai_summary', sa.Text(), nullable=True),
    sa.Column('ai_status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("content_type IN ('image/png', 'image/jpeg', 'video/mp4')", name=op.f('ck_materials_content_type')),
    sa.CheckConstraint('file_size > 0 AND file_size <= 31457280', name=op.f('ck_materials_file_size')),
    sa.CheckConstraint("ai_status IN ('done', 'failed', 'disabled')", name=op.f('ck_materials_ai_status')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_materials_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_materials')),
    sa.UniqueConstraint('stored_filename', name=op.f('uq_materials_stored_filename'))
    )
    op.create_index('ix_materials_user_id_created_at', 'materials', ['user_id', 'created_at'], unique=False)
    # Added by hand: every request goes through FastAPI, so Supabase's Data API must not
    # read this table directly. RLS with no policies blocks it (plan.md Phase 13-3).
    if op.get_bind().dialect.name == 'postgresql':
        op.execute('ALTER TABLE materials ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_materials_user_id_created_at', table_name='materials')
    op.drop_table('materials')
