from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class ModelPrediction(Base):
    __tablename__ = "model_predictions"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(50), nullable=False, index=True)
    prediction_date = Column(Date, nullable=False)
    target_date = Column(Date, nullable=False, index=True)
    predicted_value = Column(Numeric(10, 4), nullable=True)
    actual_value = Column(Numeric(10, 4), nullable=True)
    confidence_lower = Column(Numeric(10, 4), nullable=True)
    confidence_upper = Column(Numeric(10, 4), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ModelPrediction(id={self.id}, model='{self.model_name}', target_date={self.target_date})>"
