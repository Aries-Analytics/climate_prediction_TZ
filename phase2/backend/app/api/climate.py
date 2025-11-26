from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.schemas.climate_data import TimeSeries
from app.services import climate_service
from app.models.user import User
from app.models.climate_data import ClimateData
from app.utils.data_optimization import optimize_for_chart

router = APIRouter(prefix="/climate", tags=["climate"])

@router.get("/timeseries", response_model=TimeSeries)
def get_timeseries(
    variable: str = Query(..., description="Climate variable (temperature_avg, rainfall_mm, ndvi, etc.)"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    max_points: int = Query(1000, ge=100, le=10000, description="Maximum data points for chart optimization"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get time series data for a climate variable (optimized for chart rendering)"""
    result = climate_service.get_climate_timeseries(db, variable, start_date, end_date)
    
    # Return result directly - it's already a Pydantic model
    return result

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

@router.post("/batch")
def create_climate_batch(
    records: List[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Bulk create climate data records"""
    created_count = 0
    for record in records:
        try:
            # Parse date
            if isinstance(record.get('date'), str):
                record_date = datetime.strptime(record['date'], '%Y-%m-%d').date()
            else:
                record_date = record['date']
            
            climate_record = ClimateData(
                date=record_date,
                location_lat=record.get('location_lat'),
                location_lon=record.get('location_lon'),
                temperature_avg=record.get('temperature_avg'),
                rainfall_mm=record.get('rainfall_mm'),
                ndvi=record.get('ndvi'),
                enso_index=record.get('enso_index'),
                iod_index=record.get('iod_index')
            )
            db.add(climate_record)
            created_count += 1
        except Exception as e:
            print(f"Error adding record: {e}")
            continue
    
    db.commit()
    return {"message": f"Created {created_count} climate records", "count": created_count}
