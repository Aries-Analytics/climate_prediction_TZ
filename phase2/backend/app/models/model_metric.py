from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class ModelMetric(Base):
    __tablename__ = "model_metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(50), nullable=False, index=True)
    experiment_id = Column(String(100), nullable=True)
    r2_score = Column(Numeric(6, 4), nullable=True)
    rmse = Column(Numeric(10, 4), nullable=True)
    mae = Column(Numeric(10, 4), nullable=True)
    mape = Column(Numeric(6, 4), nullable=True)
    training_date = Column(DateTime(timezone=True), nullable=False, index=True)
    data_start_date = Column(Date, nullable=True)
    data_end_date = Column(Date, nullable=True)
    hyperparameters = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ModelMetric(id={self.id}, model='{self.model_name}', r2={self.r2_score})>"
