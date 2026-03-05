from sqlalchemy import Column, Integer, String, Float, DateTime, Date, JSON, Text, Numeric
from sqlalchemy.sql import func
from app.core.database import Base

class ForecastLog(Base):
    __tablename__ = "forecast_logs"
    
    id = Column(String(50), primary_key=True, index=True) # UUID
    issued_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=False)
    region_id = Column(String(50), nullable=False, index=True)
    model_version = Column(String(100), nullable=False)
    
    forecast_type = Column(String(50), nullable=False) # e.g. "rainfall", "flood", "crop_failure"
    forecast_value = Column(Numeric(5, 4), nullable=False) # raw probability from the model 0.0 to 1.0
    forecast_distribution = Column(JSON, nullable=True) # Confidence intervals or array of probabilities
    
    threshold_used = Column(Numeric(7, 2), nullable=True) # e.g. 140.0 for 140mm
    lead_time_days = Column(Integer, nullable=False)
    
    data_snapshot_id = Column(String(100), nullable=True) # For tying back to the database state
    
    status = Column(String(20), default="pending", nullable=False) # pending, evaluated
    
    # Post-evaluation metrics
    observed_value = Column(Numeric(7, 2), nullable=True)
    brier_score = Column(Numeric(5, 4), nullable=True)
    
    def __repr__(self):
        return f"<ForecastLog(id={self.id}, type='{self.forecast_type}', issued={self.issued_at}, value={self.forecast_value})>"
