"""add_location_to_forecasts

Revision ID: 4d23088e9e0f
Revises: 7081af600314
Create Date: 2026-01-04 23:19:25.103077

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4d23088e9e0f'
down_revision = '7081af600314'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Delete existing forecasts (they have no location tracking)
    op.execute('DELETE FROM forecast_validation')
    op.execute('DELETE FROM forecast_recommendations')
    op.execute('DELETE FROM forecasts')
    
    # Step 2: Drop old unique constraint (without location_id)
    op.drop_constraint('uq_forecast_date_target_type', 'forecasts', type_='unique')
    
    # Step 3: Add location_id column (non-nullable with foreign key)
    op.add_column('forecasts', sa.Column('location_id', sa.Integer(), nullable=False))
    op.create_foreign_key('fk_forecasts_location', 'forecasts', 'locations', ['location_id'], ['id'])
    op.create_index('idx_forecasts_location', 'forecasts', ['location_id'])
    
    # Step 4: Add new unique constraint (with location_id)
    op.create_unique_constraint('uq_forecast_date_target_type_location', 'forecasts', 
                                ['forecast_date', 'target_date', 'trigger_type', 'location_id'])


def downgrade() -> None:
    # Remove new constraint
    op.drop_constraint('uq_forecast_date_target_type_location', 'forecasts', type_='unique')
    
    # Remove location column and index
    op.drop_index('idx_forecasts_location', 'forecasts')
    op.drop_constraint('fk_forecasts_location', 'forecasts', type_='foreignkey')
    op.drop_column('forecasts', 'location_id')
    
    # Restore old constraint
    op.create_unique_constraint('uq_forecast_date_target_type', 'forecasts',
                                ['forecast_date', 'target_date', 'trigger_type'])
