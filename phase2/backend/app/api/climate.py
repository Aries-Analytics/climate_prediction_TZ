from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.schemas.climate_data import TimeSeries
from app.services import climate_service
from app.models.user import User

router = APIRouter(prefix="/climate", tags=["climate"])

@router.get("/timeseries", response_model=TimeSeries)
def get_timeseries(
    variable: str = Query(..., description="Climate variable (temperature_avg, rainfall_mm, ndvi, etc.)"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get time series data for a climate variable"""
    return climate_service.get_climate_timeseries(db, variable, start_date, end_date)

@router.get("/anomalies")
def get_anomalies(
    variable: str = Query(..., description="Climate variable"),
    threshold: float = Query(2.0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detected anomalies for a climate variable"""
    return climate_service.calculate_anomalies(db, variable, threshold)

@router.get("/correlations")
def get_correlations(
    variables: List[str] = Query(..., description="List of variables to correlate"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get correlation matrix for climate variables"""
    return climate_service.get_correlation_matrix(db, variables)

@router.get("/seasonal")
def get_seasonal(
    variable: str = Query(..., description="Climate variable"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get seasonal patterns for a variable"""
    return climate_service.get_seasonal_patterns(db, variable)
