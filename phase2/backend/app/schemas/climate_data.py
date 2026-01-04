from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional
from decimal import Decimal

def to_camel(string: str) -> str:
    """Convert snake_case to camelCase"""
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

class ClimateDataBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
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
    
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )

class TimeSeriesPoint(BaseModel):
    date: date
    median: float
    min: float
    max: float
    # Deprecated: kept for backward compatibility
    value: Optional[float] = None

class TimeSeries(BaseModel):
    variable: str
    data: list[TimeSeriesPoint]
