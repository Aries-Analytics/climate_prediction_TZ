from pydantic import BaseModel
from typing import List, Dict, Any

class PortfolioMetrics(BaseModel):
    total_premium_income: float
    expected_payouts: float
    loss_ratio: float
    total_policies: int
    active_policies: int
    trigger_distribution: Dict[str, int]  # trigger_type -> count
    geographic_distribution: Dict[str, int]  # region -> count
    risk_score: float  # 0-100

class ScenarioParameters(BaseModel):
    scenario_name: str
    rainfall_change_pct: float  # percentage change
    temperature_change_celsius: float
    duration_months: int

class ScenarioResult(BaseModel):
    scenario_name: str
    parameters: ScenarioParameters
    estimated_triggers: int
    estimated_payouts: float
    projected_loss_ratio: float
    risk_level: str  # "low", "medium", "high"
    impact_summary: str

class Recommendation(BaseModel):
    priority: str  # "high", "medium", "low"
    category: str  # "risk_mitigation", "portfolio_adjustment", "monitoring"
    title: str
    description: str
    action_items: List[str]
