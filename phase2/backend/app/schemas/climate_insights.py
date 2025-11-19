from pydantic import BaseModel
from datetime import date
from typing import List, Dict

class Anomaly(BaseModel):
    date: date
    variable: str
    value: float
    expected_value: float
    deviation: float
    severity: str  # "low", "medium", "high"

class CorrelationMatrix(BaseModel):
    variables: List[str]
    matrix: List[List[float]]

class SeasonalPattern(BaseModel):
    variable: str
    monthly_averages: Dict[int, float]  # month (1-12) -> average value
    seasonal_trend: str  # "increasing", "decreasing", "stable"
