from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class TriggerAlert(Base):
    """
    Stores actionable insurance alerts when a climate forecast breaches a 
    calibrated threshold (e.g., Rainfall < 120mm during Flowering stage).
    """
    __tablename__ = "trigger_alerts"

    id = Column(Integer, primary_key=True, index=True)
    climate_forecast_id = Column(Integer, ForeignKey('climate_forecasts.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Alert Details
    alert_type = Column(String(50), nullable=False)     # e.g., 'rainfall_deficit', 'excessive_rainfall', 'ndvi_anomaly'
    severity = Column(String(20), nullable=False)       # 'critical', 'warning', 'watch'
    phenology_stage = Column(String(50), nullable=False) # e.g., 'germination', 'flowering', 'grain_fill'
    
    # Threshold Data (Snapshot at time of alert)
    threshold_value = Column(Numeric(10, 2), nullable=False)  # The rule value (e.g., 120.00)
    forecast_value = Column(Numeric(10, 2), nullable=False)   # The predicted value (e.g., 85.00)
    deviation = Column(Numeric(10, 2), nullable=True)         # Diff (e.g., -35.00)
    
    # Actionable Info
    recommended_action = Column(String, nullable=True)        # e.g., "Prepare supplemental irrigation"
    urgency_days = Column(Integer, nullable=True)             # How soon action is needed
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    climate_forecast = relationship("ClimateForecast", back_populates="trigger_alerts")

    # Indexes
    __table_args__ = (
        Index('idx_trigger_alerts_severity', 'severity'),
        Index('idx_trigger_alerts_type', 'alert_type'),
    )

    def __repr__(self):
        return f"<TriggerAlert(id={self.id}, type='{self.alert_type}', severity='{self.severity}', stage='{self.phenology_stage}')>"
