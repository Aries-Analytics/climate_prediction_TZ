from sqlalchemy import Column, Integer, Date, Numeric, DateTime, Index, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base

class ClimateData(Base):
    __tablename__ = "climate_data"
    
    # Table constraints and indexes
    __table_args__ = (
        # UNIQUE CONSTRAINT: Prevent duplicate entries for same date and location
        UniqueConstraint('date', 'location_lat', 'location_lon', name='uix_date_location'),
        # Composite indexes for common query patterns
        Index('idx_climate_date_location', 'date', 'location_lat', 'location_lon'),
        Index('idx_climate_created_at', 'created_at'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    location_lat = Column(Numeric(10, 6), nullable=True)
    location_lon = Column(Numeric(10, 6), nullable=True)
    temperature_avg = Column(Numeric(5, 2), nullable=True)
    rainfall_mm = Column(Numeric(7, 2), nullable=True)
    ndvi = Column(Numeric(4, 3), nullable=True)
    soil_moisture = Column(Numeric(5, 3), nullable=True)  # Volumetric soil moisture (0-1 fraction)
    enso_index = Column(Numeric(5, 3), nullable=True)
    iod_index = Column(Numeric(5, 3), nullable=True)
    # Atmospheric columns (fetched by NASA POWER / ERA5 but previously not stored)
    humidity_pct = Column(Numeric(5, 2), nullable=True)         # General humidity %
    rel_humidity_pct = Column(Numeric(5, 2), nullable=True)     # Relative humidity % (NASA POWER RH2M)
    dewpoint_2m = Column(Numeric(6, 2), nullable=True)          # Dewpoint temperature °C (ERA5 d2m)
    wind_speed_ms = Column(Numeric(5, 2), nullable=True)        # Wind speed m/s (derived from u/v)
    wind_u_10m = Column(Numeric(6, 3), nullable=True)           # U-component of wind m/s (ERA5 u10)
    wind_v_10m = Column(Numeric(6, 3), nullable=True)           # V-component of wind m/s (ERA5 v10)
    wind_direction_deg = Column(Numeric(5, 1), nullable=True)   # Wind direction degrees (derived)
    surface_pressure = Column(Numeric(8, 1), nullable=True)     # Surface pressure Pa (ERA5 sp)
    vpd_kpa = Column(Numeric(5, 3), nullable=True)              # Vapor pressure deficit kPa (derived)
    solar_rad_wm2 = Column(Numeric(6, 2), nullable=True)        # Solar radiation W/m² (NASA POWER)
    pet_mm = Column(Numeric(6, 2), nullable=True)               # Potential evapotranspiration mm (derived)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ClimateData(id={self.id}, date={self.date}, location=({self.location_lat}, {self.location_lon}))>"
