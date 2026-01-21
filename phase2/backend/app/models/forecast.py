from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    forecast_date = Column(Date, nullable=False, index=True)  # When forecast was made
    target_date = Column(Date, nullable=False, index=True)  # Date being predicted
    horizon_months = Column(Integer, nullable=False)  # 3, 4, 5, or 6
    trigger_type = Column(String(50), nullable=False, index=True)  # drought, flood, crop_failure
    probability = Column(Numeric(5, 4), nullable=False)  # 0.0000 to 1.0000
    confidence_lower = Column(Numeric(5, 4), nullable=False)
    confidence_upper = Column(Numeric(5, 4), nullable=False)
    model_version = Column(String(100), nullable=True)
    expected_deficit = Column(Numeric(7, 2), nullable=True)  # Expected rainfall deficit in mm
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    location = relationship("Location", back_populates="forecasts")
    recommendations = relationship("ForecastRecommendation", back_populates="forecast", cascade="all, delete-orphan")
    validations = relationship("ForecastValidation", back_populates="forecast", cascade="all, delete-orphan")

    # Composite indexes and constraints
    __table_args__ = (
        UniqueConstraint('forecast_date', 'target_date', 'trigger_type', 'location_id', name='uq_forecast_date_target_type_location'),
        Index('idx_forecasts_target', 'target_date', 'trigger_type'),
        Index('idx_forecasts_created', 'created_at'),
        Index('idx_forecasts_probability', 'probability'),
        Index('idx_forecasts_location', 'location_id'),
    )

    def __repr__(self):
        return f"<Forecast(id={self.id}, type='{self.trigger_type}', target={self.target_date}, prob={self.probability})>"


class ForecastRecommendation(Base):
    __tablename__ = "forecast_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    forecast_id = Column(Integer, ForeignKey('forecasts.id', ondelete='CASCADE'), nullable=False, index=True)
    recommendation_text = Column(String, nullable=False)
    priority = Column(String(20), nullable=False)  # high, medium, low
    action_timeline = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    forecast = relationship("Forecast", back_populates="recommendations")

    def __repr__(self):
        return f"<ForecastRecommendation(id={self.id}, forecast_id={self.forecast_id}, priority='{self.priority}')>"


class ForecastValidation(Base):
    __tablename__ = "forecast_validation"

    id = Column(Integer, primary_key=True, index=True)
    forecast_id = Column(Integer, ForeignKey('forecasts.id', ondelete='CASCADE'), nullable=False, index=True)
    actual_trigger_id = Column(Integer, ForeignKey('trigger_events.id', ondelete='SET NULL'), nullable=True, index=True)
    was_correct = Column(Integer, nullable=False)  # Using Integer for Boolean (0 or 1)
    probability_error = Column(Numeric(5, 4), nullable=True)
    brier_score = Column(Numeric(5, 4), nullable=True)
    validated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    forecast = relationship("Forecast", back_populates="validations")

    __table_args__ = (
        Index('idx_validation_forecast', 'forecast_id'),
        Index('idx_validation_trigger', 'actual_trigger_id'),
    )

    def __repr__(self):
        return f"<ForecastValidation(id={self.id}, forecast_id={self.forecast_id}, correct={bool(self.was_correct)})>"
