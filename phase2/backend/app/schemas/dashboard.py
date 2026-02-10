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

# Phase-Based Coverage Model Schemas (Production)
class PhaseStats(BaseModel):
    """Statistics for a single rice growth phase"""
    phase_name: str
    duration_days: int
    rainfall_mm: float
    drought_trigger_mm: float
    drought_payout: float
    flood_payout: float
    total_payout: float
    status: str  # "normal", "drought_risk", "flood_risk"

class SeasonalForecast(BaseModel):
    """Seasonal forecast for rice insurance"""
    location: str
    season: str
    predicted_rainfall_mm: float
    drought_probability: float
    flood_probability: float
    expected_payout_per_farmer: float
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    phase_breakdown: List[PhaseStats]

class DashboardSummary(BaseModel):
    """Complete dashboard data"""
    executive_kpis: ExecutiveKPIs
    seasonal_forecast: SeasonalForecast
    loss_ratio_trend: LossRatioTrend
    sustainability: SustainabilityStatus
