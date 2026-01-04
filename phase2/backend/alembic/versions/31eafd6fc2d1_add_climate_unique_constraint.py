"""add_climate_unique_constraint

Revision ID: 31eafd6fc2d1
Revises: 005
Create Date: 2026-01-01 05:47:23.230068

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '31eafd6fc2d1'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Remove duplicate records, keeping the first occurrence by ID
    # This cleans up existing duplicates before adding the unique constraint
    op.execute("""
        DELETE FROM climate_data
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM climate_data
            GROUP BY date, location_lat, location_lon
        );
    """)
    
    # Step 2: Add unique constraint to prevent future duplicates
    op.create_unique_constraint(
        'uix_date_location',
        'climate_data',
        ['date', 'location_lat', 'location_lon']
    )
    
    print("SUCCESS: Removed duplicate climate data records")
    print("SUCCESS: Added unique constraint on (date, location_lat, location_lon)")


def downgrade() -> None:
    # Remove the unique constraint
    op.drop_constraint('uix_date_location', 'climate_data', type_='unique')
