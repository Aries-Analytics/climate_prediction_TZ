"""add_ndvi_observations_table

Revision ID: f3a9b2c1d8e7
Revises: d5c0ade1d7a9
Create Date: 2026-03-30 08:00:00.000000

Shadow-run proxy validation table.
Stores daily Kilombero NDVI observations (MODIS MOD13A2 via GEE) alongside
forecast_logs entries so we can correlate drought/flood signals with
vegetation stress after the evaluation window closes.
"""
from alembic import op
import sqlalchemy as sa

revision = 'f3a9b2c1d8e7'
down_revision = 'd5c0ade1d7a9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ndvi_observations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_date', sa.Date(), nullable=False,
                  comment='Pipeline run date this observation corresponds to'),
        sa.Column('observed_date', sa.Date(), nullable=False,
                  comment='Date of the actual satellite pass used (nearest within ±3 days)'),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('ndvi_mean', sa.Numeric(precision=5, scale=4), nullable=True,
                  comment='Mean NDVI across Kilombero bounding box'),
        sa.Column('ndvi_anomaly', sa.Numeric(precision=6, scale=4), nullable=True,
                  comment='Deviation from 2015-2024 same-month historical mean'),
        sa.Column('pixel_coverage', sa.Numeric(precision=5, scale=2), nullable=True,
                  comment='Percentage of valid (cloud-free) pixels'),
        sa.Column('source', sa.String(length=50), nullable=False,
                  server_default='MODIS_MOD13A2'),
        sa.Column('is_backfilled', sa.Boolean(), nullable=False,
                  server_default='false',
                  comment='True if inserted by backfill script, False if collected live'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('run_date', name='uq_ndvi_observations_run_date'),
    )
    op.create_index('ix_ndvi_observations_run_date', 'ndvi_observations', ['run_date'])
    op.create_index('ix_ndvi_observations_observed_date', 'ndvi_observations', ['observed_date'])


def downgrade() -> None:
    op.drop_index('ix_ndvi_observations_observed_date', table_name='ndvi_observations')
    op.drop_index('ix_ndvi_observations_run_date', table_name='ndvi_observations')
    op.drop_table('ndvi_observations')
