from sqlalchemy import Column, Integer, Date, Numeric, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class ClimateData(Base):
    __tablename__ = "climate_data"

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
