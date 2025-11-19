from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class TriggerEvent(Base):
    __tablename__ = "trigger_events"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    trigger_type = Column(String(50), nullable=False, index=True)  # drought, flood, crop_failure
    confidence = Column(Numeric(4, 3), nullable=True)  # 0.0 to 1.0
    severity = Column(Numeric(4, 3), nullable=True)  # 0.0 to 1.0
    payout_amount = Column(Numeric(10, 2), nullable=True)
    location_lat = Column(Numeric(10, 6), nullable=True)
    location_lon = Column(Numeric(10, 6), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<TriggerEvent(id={self.id}, type='{self.trigger_type}', date={self.date}, payout={self.payout_amount})>"
