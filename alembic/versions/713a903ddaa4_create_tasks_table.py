"""create tasks table

Revision ID: 713a903ddaa4
Revises: 
Create Date: 2025-09-05 11:26:14.089898

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '713a903ddaa4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Upgrade schema."""
    # Create a dedicated PostgreSQL ENUM type for status
    task_status = sa.Enum('pending', 'in-progress', 'completed', name='taskstatus')
    task_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', task_status, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_tasks_id'), table_name='tasks')
    op.drop_table('tasks')
    # Drop ENUM type
    task_status = sa.Enum('pending', 'in-progress', 'completed', name='taskstatus')
    task_status.drop(op.get_bind(), checkfirst=True)
