"""Add location name to trigger_events

Revision ID: 7081af600314
Revises: 31eafd6fc2d1
Create Date: 2026-01-02 11:25:12.783213

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7081af600314'
down_revision = '31eafd6fc2d1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add location column to trigger_events
    op.add_column('trigger_events', sa.Column('location', sa.String(100), nullable=True))


def downgrade() -> None:
    # Remove location column from trigger_events
    op.drop_column('trigger_events', 'location')
