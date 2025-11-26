"""increase mape precision

Revision ID: 003
Revises: 002
Create Date: 2025-11-22

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Alter mape column to allow larger percentage values
    op.alter_column('model_metrics', 'mape',
                    type_=sa.Numeric(10, 4),
                    existing_type=sa.Numeric(6, 4),
                    existing_nullable=True)


def downgrade():
    # Revert to original precision
    op.alter_column('model_metrics', 'mape',
                    type_=sa.Numeric(6, 4),
                    existing_type=sa.Numeric(10, 4),
                    existing_nullable=True)
