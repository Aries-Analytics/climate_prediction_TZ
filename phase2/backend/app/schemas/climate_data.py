from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from decimal import Decimal

class ClimateDataBase(BaseModel):
    date: date
    location_lat: Optional[Decimal] = None
    location_lon: Optional[Decimal] = None
    temperature_avg: Optional[Decimal] = None
    rainfall_mm: Optional[Decimal] = None
    ndvi: Optional[Decimal] = None
    enso_index: Optional[Decimal] = None
    iod_index: Optional[Decimal] = None

class ClimateDataCreate(ClimateDataBase):
    pass

class ClimateDataResponse(ClimateDataBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class TimeSeriesPoint(BaseModel):
    date: date
    value: float

class TimeSeries(BaseModel):
    variable: str
    data: list[TimeSeriesPoint]
