from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ClimateForecast(Base):
    """
    Stores raw climate variable forecasts (Rainfall, NDVI, Soil Moisture).
    This replaces the legacy Forecast model which stored 'trigger types'.
    """
    __tablename__ = "climate_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    forecast_date = Column(Date, nullable=False, index=True)  # When the forecast was generated
    target_date = Column(Date, nullable=False, index=True)    # The date being predicted
    horizon_days = Column(Integer, nullable=False)            # e.g., 30, 60, 90
    
    # Climate Variables (At least one should be populated)
    rainfall_mm = Column(Numeric(8, 2), nullable=True)        # Predicted rainfall amount
    rainfall_lower = Column(Numeric(8, 2), nullable=True)     # 95% Confidence Interval Lower Bound
    rainfall_upper = Column(Numeric(8, 2), nullable=True)     # 95% Confidence Interval Upper Bound
    
    ndvi_value = Column(Numeric(5, 4), nullable=True)         # Normalized Difference Vegetation Index (-1 to 1)
    ndvi_lower = Column(Numeric(5, 4), nullable=True)
    ndvi_upper = Column(Numeric(5, 4), nullable=True)
    
    soil_moisture_pct = Column(Numeric(5, 2), nullable=True)  # Volumetric Soil Moisture %
    soil_moisture_lower = Column(Numeric(5, 2), nullable=True)
    soil_moisture_upper = Column(Numeric(5, 2), nullable=True)
    
    # Metadata
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=False, index=True)
    model_version = Column(String(100), nullable=True)        # e.g. "rf_ensemble_v2.1"
    season = Column(String(20), nullable=True)                # 'wet_season', 'dry_season'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    location = relationship("Location", back_populates="climate_forecasts")
    trigger_alerts = relationship("TriggerAlert", back_populates="climate_forecast", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        UniqueConstraint('forecast_date', 'target_date', 'location_id', name='uq_climate_forecast_entry'),
        Index('idx_climate_forecasts_target', 'target_date'),
        Index('idx_climate_forecasts_location', 'location_id'),
    )

    def __repr__(self):
        return f"<ClimateForecast(id={self.id}, target={self.target_date}, rainfall={self.rainfall_mm}mm)>"
