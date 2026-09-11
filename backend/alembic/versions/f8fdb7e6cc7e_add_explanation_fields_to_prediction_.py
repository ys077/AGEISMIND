"""Add explanation fields to prediction factors

Revision ID: f8fdb7e6cc7e
Revises: de76a04a8eaa
Create Date: 2026-09-10 19:54:41.979069
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8fdb7e6cc7e'
down_revision: Union[str, None] = 'de76a04a8eaa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('prediction_factors', sa.Column('feature_value', sa.String(length=255), nullable=True))
    op.add_column('prediction_factors', sa.Column('explanation_text', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('prediction_factors', 'explanation_text')
    op.drop_column('prediction_factors', 'feature_value')
