from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime
from typing import Optional
from decimal import Decimal

def to_camel(string: str) -> str:
    """Convert snake_case to camelCase"""
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

class TriggerEventBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    date: date
    trigger_type: str = Field(..., pattern="^(drought|flood|crop_failure)$")
    confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    severity: Optional[Decimal] = None  # Can be larger values for crop failure
    payout_amount: Optional[Decimal] = None
    location_lat: Optional[Decimal] = None
    location_lon: Optional[Decimal] = None

class TriggerEventCreate(TriggerEventBase):
    pass

class TriggerEventResponse(TriggerEventBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )

class TriggerForecast(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    target_date: date
    trigger_type: str
    probability: float = Field(..., ge=0, le=1)
    confidence_lower: float = Field(..., ge=0, le=1)
    confidence_upper: float = Field(..., ge=0, le=1)

class EarlyWarning(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    alert_type: str
    severity: str = Field(..., pattern="^(low|medium|high)$")
    message: str
    trigger_probability: float
    target_date: date
    recommended_action: str

class TimelineEvent(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    date: date
    trigger_type: str
    count: int
    total_payout: float
