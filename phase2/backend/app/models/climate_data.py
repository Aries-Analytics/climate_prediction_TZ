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
    enso_index = Column(Numeric(5, 3), nullable=True)
    iod_index = Column(Numeric(5, 3), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ClimateData(id={self.id}, date={self.date}, location=({self.location_lat}, {self.location_lon}))>"
