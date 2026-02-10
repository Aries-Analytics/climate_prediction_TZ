"""add soil moisture column

Revision ID: 006_add_soil_moisture
Revises: 005_add_pipeline_tracking_tables
Create Date: 2026-02-02 21:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_add_soil_moisture'
down_revision = '959c8edee2a3'  # create_simulation_tables
branch_labels = None
depends_on = None


def upgrade():
    """Add soil_moisture column to climate_data table"""
    # Add soil_moisture column
    op.add_column('climate_data', 
        sa.Column('soil_moisture', sa.Numeric(precision=5, scale=3), nullable=True,
                  comment='Volumetric soil moisture (0-1 fraction)')
    )
    
    # Add index for soil_moisture queries
    op.create_index('idx_climate_soil_moisture', 'climate_data', ['soil_moisture'])


def downgrade():
    """Remove soil_moisture column from climate_data table"""
    op.drop_index('idx_climate_soil_moisture', table_name='climate_data')
    op.drop_column('climate_data', 'soil_moisture')
