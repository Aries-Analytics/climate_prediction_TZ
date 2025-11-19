from pydantic import BaseModel
from datetime import date
from typing import List

class TriggerRate(BaseModel):
    trigger_type: str
    rate: float
    count: int
    target_min: float
    target_max: float
    status: str  # "within_target", "below_target", "above_target"

class ExecutiveKPIs(BaseModel):
    flood_trigger_rate: TriggerRate
    drought_trigger_rate: TriggerRate
    crop_failure_trigger_rate: TriggerRate
    combined_trigger_rate: float
    loss_ratio: float
    sustainability_status: str  # "sustainable", "warning", "unsustainable"
    total_triggers_ytd: int
    estimated_payouts_ytd: float

class TrendPoint(BaseModel):
    date: date
    value: float

class LossRatioTrend(BaseModel):
    data: List[TrendPoint]
    target_threshold: float

class SustainabilityStatus(BaseModel):
    status: str
    loss_ratio: float
    threshold: float
    message: str
