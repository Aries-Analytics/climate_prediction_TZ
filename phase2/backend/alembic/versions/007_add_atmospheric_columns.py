"""add atmospheric columns for feature alignment

Revision ID: 007_add_atmospheric_columns
Revises: 006_add_soil_moisture
Create Date: 2026-02-23 12:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007_add_atmospheric_columns'
down_revision = '006_add_soil_moisture'
branch_labels = None
depends_on = None


def upgrade():
    """Add atmospheric/environmental columns to climate_data table.
    
    These columns store data already fetched by NASA POWER and ERA5 ingestion
    but previously discarded at DB storage time. Required for the 15 model 
    features that depend on humidity, wind, solar, pressure, dewpoint, VPD, and PET.
    """
    columns = [
        ('humidity_pct', sa.Numeric(precision=5, scale=2), 'General humidity percentage'),
        ('rel_humidity_pct', sa.Numeric(precision=5, scale=2), 'Relative humidity % from NASA POWER RH2M'),
        ('dewpoint_2m', sa.Numeric(precision=6, scale=2), 'Dewpoint temperature in Celsius from ERA5'),
        ('wind_speed_ms', sa.Numeric(precision=5, scale=2), 'Wind speed m/s derived from u/v components'),
        ('wind_u_10m', sa.Numeric(precision=6, scale=3), 'U-component of wind m/s from ERA5'),
        ('wind_v_10m', sa.Numeric(precision=6, scale=3), 'V-component of wind m/s from ERA5'),
        ('wind_direction_deg', sa.Numeric(precision=5, scale=1), 'Wind direction in degrees derived from u/v'),
        ('surface_pressure', sa.Numeric(precision=8, scale=1), 'Surface pressure in Pa from ERA5'),
        ('vpd_kpa', sa.Numeric(precision=5, scale=3), 'Vapor pressure deficit in kPa'),
        ('solar_rad_wm2', sa.Numeric(precision=6, scale=2), 'Solar radiation W/m2 from NASA POWER'),
        ('pet_mm', sa.Numeric(precision=6, scale=2), 'Potential evapotranspiration in mm'),
    ]
    
    for col_name, col_type, comment in columns:
        op.add_column('climate_data',
            sa.Column(col_name, col_type, nullable=True, comment=comment)
        )


def downgrade():
    """Remove atmospheric columns from climate_data table"""
    columns = [
        'humidity_pct', 'rel_humidity_pct', 'dewpoint_2m',
        'wind_speed_ms', 'wind_u_10m', 'wind_v_10m', 'wind_direction_deg',
        'surface_pressure', 'vpd_kpa', 'solar_rad_wm2', 'pet_mm',
    ]
    for col_name in columns:
        op.drop_column('climate_data', col_name)
