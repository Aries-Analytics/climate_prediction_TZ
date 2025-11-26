"""increase severity precision

Revision ID: 002
Revises: 001
Create Date: 2025-11-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Alter severity column to allow larger values
    op.alter_column('trigger_events', 'severity',
                    type_=sa.Numeric(10, 3),
                    existing_type=sa.Numeric(4, 3),
                    existing_nullable=True)


def downgrade():
    # Revert to original precision
    op.alter_column('trigger_events', 'severity',
                    type_=sa.Numeric(4, 3),
                    existing_type=sa.Numeric(10, 3),
                    existing_nullable=True)
