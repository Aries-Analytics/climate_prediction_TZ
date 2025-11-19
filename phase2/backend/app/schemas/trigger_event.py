from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from decimal import Decimal

class TriggerEventBase(BaseModel):
    date: date
    trigger_type: str = Field(..., pattern="^(drought|flood|crop_failure)$")
    confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    severity: Optional[Decimal] = Field(None, ge=0, le=1)
    payout_amount: Optional[Decimal] = None
    location_lat: Optional[Decimal] = None
    location_lon: Optional[Decimal] = None

class TriggerEventCreate(TriggerEventBase):
    pass

class TriggerEventResponse(TriggerEventBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class TriggerForecast(BaseModel):
    target_date: date
    trigger_type: str
    probability: float = Field(..., ge=0, le=1)
    confidence_lower: float = Field(..., ge=0, le=1)
    confidence_upper: float = Field(..., ge=0, le=1)

class EarlyWarning(BaseModel):
    alert_type: str
    severity: str = Field(..., pattern="^(low|medium|high)$")
    message: str
    trigger_probability: float
    target_date: date
    recommended_action: str

class TimelineEvent(BaseModel):
    date: date
    trigger_type: str
    count: int
    total_payout: float
