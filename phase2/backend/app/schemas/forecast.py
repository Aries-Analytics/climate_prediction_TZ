from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase"""
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


# Forecast Schemas
class ForecastBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        by_alias=True  # CRITICAL: Serialize using camelCase aliases
    )
    
    forecast_date: date
    target_date: date
    horizon_months: int = Field(..., ge=3, le=6, description="Forecast horizon in months (3-6)")
    trigger_type: str = Field(..., pattern="^(drought|flood|crop_failure)$")
    probability: float = Field(..., ge=0, le=1, description="Probability of trigger event (0-1)")
    confidence_lower: float = Field(..., ge=0, le=1, description="Lower confidence bound")
    confidence_upper: float = Field(..., ge=0, le=1, description="Upper confidence bound")
    model_version: Optional[str] = None
    location_id: int

    @field_validator('confidence_lower', 'confidence_upper')
    @classmethod
    def validate_confidence_bounds(cls, v):
        if not (0 <= v <= 1):
            raise ValueError('Confidence bounds must be between 0 and 1')
        return v


class ForecastCreate(ForecastBase):
    expected_deficit: Optional[float] = None


class ForecastResponse(ForecastBase):
    id: int
    created_at: datetime
    is_stale: bool = False
    
    # UI Helpers (Dynamic)
    expected_deficit: Optional[float] = None
    threshold_value: Optional[float] = None
    stage: Optional[str] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
        by_alias=True
    )


# Recommendation Schemas
class RecommendationBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        by_alias=True
    )
    
    recommendation_text: str
    priority: str = Field(..., pattern="^(high|medium|low)$")
    action_timeline: Optional[str] = None


class RecommendationCreate(RecommendationBase):
    forecast_id: int


class RecommendationResponse(RecommendationBase):
    id: int
    forecast_id: int
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
        by_alias=True
    )


# Forecast with Recommendations
class ForecastWithRecommendations(ForecastResponse):
    recommendations: List[RecommendationResponse] = []
    
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
        by_alias=True
    )


# Validation Schemas
class ValidationBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        by_alias=True
    )
    
    forecast_id: int
    actual_trigger_id: Optional[int] = None
    was_correct: bool
    probability_error: Optional[float] = None
    brier_score: Optional[float] = None


class ValidationCreate(ValidationBase):
    pass


class ValidationResponse(ValidationBase):
    id: int
    validated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
        by_alias=True
    )


# Request/Response Schemas for API
class ForecastGenerateRequest(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        by_alias=True
    )
    
    start_date: Optional[date] = None
    horizons: List[int] = Field(default=[3, 4, 5, 6], description="Forecast horizons in months")

    @field_validator('horizons')
    @classmethod
    def validate_horizons(cls, v):
        if not all(3 <= h <= 6 for h in v):
            raise ValueError('All horizons must be between 3 and 6 months')
        return v


class ForecastQueryParams(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        by_alias=True
    )
    
    trigger_type: Optional[str] = Field(None, pattern="^(drought|flood|crop_failure)$")
    min_probability: Optional[float] = Field(None, ge=0, le=1)
    horizon_months: Optional[int] = Field(None, ge=3, le=6)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ValidationMetrics(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        by_alias=True
    )
    
    trigger_type: str
    horizon_months: int
    total_forecasts: int
    correct_forecasts: int
    accuracy: float
    precision: Optional[float] = None
    recall: Optional[float] = None
    avg_brier_score: Optional[float] = None


# NEW: Location Risk Summary Schemas
class LocationRiskSummary(BaseModel):
    """Schema for location risk summary response"""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        by_alias=True
    )
    
    location_id: int
    location_name: str
    latitude: float
    longitude: float
    drought_probability: float = Field(..., ge=0, le=1)
    flood_probability: float = Field(..., ge=0, le=1)
    crop_failure_probability: float = Field(..., ge=0, le=1)
    overall_risk_index: float = Field(..., ge=0, le=1)
    risk_level: str = Field(..., pattern="^(low|medium|high)$")
    estimated_payout: float = Field(0.0, ge=0)


class LocationRiskSummaryResponse(BaseModel):
    """Response wrapper for location risk summary endpoint"""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        by_alias=True
    )
    
    locations: List[LocationRiskSummary]
    horizon_months: int
    total_locations: int
