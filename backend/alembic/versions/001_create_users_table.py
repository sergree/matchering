"""
Create users table.

Revision ID: 001
Revises: 
Create Date: 2024-09-14 01:21:24.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import expression

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column(
            'is_active',
            sa.Boolean(),
            server_default=expression.true(),
            nullable=False
        ),
        sa.Column(
            'is_superuser',
            sa.Boolean(),
            server_default=expression.false(),
            nullable=False
        ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_users_email'),
        'users',
        ['email'],
        unique=True
    )
    op.create_index(
        op.f('ix_users_id'),
        'users',
        ['id'],
        unique=False
    )

def downgrade() -> None:
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')