from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.forecast import (
    ForecastResponse,
    ForecastWithRecommendations,
    ForecastGenerateRequest,
    ValidationMetrics
)
from app.services import forecast_service

router = APIRouter(prefix="/forecasts", tags=["forecasts"])


@router.get("", response_model=List[ForecastResponse])
def get_forecasts(
    trigger_type: Optional[str] = Query(None, regex="^(drought|flood|crop_failure)$"),
    min_probability: Optional[float] = Query(None, ge=0, le=1),
    horizon_months: Optional[int] = Query(None, ge=3, le=6),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get forecasts with optional filters
    
    - **trigger_type**: Filter by trigger type (drought, flood, crop_failure)
    - **min_probability**: Minimum probability threshold (0-1)
    - **horizon_months**: Filter by forecast horizon (3-6 months)
    - **start_date**: Filter by target date start
    - **end_date**: Filter by target date end
    
    Returns list of forecasts matching the criteria.
    """
    try:
        forecasts = forecast_service.get_forecasts(
            db=db,
            trigger_type=trigger_type,
            min_probability=min_probability,
            horizon_months=horizon_months,
            start_date=start_date,
            end_date=end_date
        )
        return forecasts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve forecasts: {str(e)}")


@router.get("/latest", response_model=List[ForecastResponse])
def get_latest_forecasts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the most recent forecasts for all trigger types and horizons
    
    Returns forecasts from the latest forecast generation run.
    """
    try:
        forecasts = forecast_service.get_latest_forecasts(db)
        
        if not forecasts:
            raise HTTPException(status_code=404, detail="No forecasts found")
        
        return forecasts
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve latest forecasts: {str(e)}")


@router.get("/recommendations", response_model=List[ForecastWithRecommendations])
def get_forecast_recommendations(
    min_probability: Optional[float] = Query(0.3, ge=0, le=1),
    trigger_type: Optional[str] = Query(None, regex="^(drought|flood|crop_failure)$"),
    priority: Optional[str] = Query(None, regex="^(high|medium|low)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get forecasts with actionable recommendations
    
    - **min_probability**: Minimum probability threshold (default: 0.3)
    - **trigger_type**: Filter by trigger type
    - **priority**: Filter by recommendation priority (high, medium, low)
    
    Returns forecasts with their associated recommendations.
    """
    try:
        forecasts_with_recs = forecast_service.get_recommendations(
            db=db,
            min_probability=min_probability,
            trigger_type=trigger_type,
            priority=priority
        )
        return forecasts_with_recs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recommendations: {str(e)}")


@router.post("/generate", response_model=List[ForecastResponse])
def generate_forecasts(
    request: ForecastGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger manual forecast generation
    
    - **start_date**: Starting date for forecasts (defaults to today)
    - **horizons**: List of forecast horizons in months (default: [3, 4, 5, 6])
    
    Generates new forecasts for all trigger types and specified horizons.
    """
    try:
        forecasts = forecast_service.generate_forecasts(
            db=db,
            start_date=request.start_date,
            horizons=request.horizons
        )
        
        if not forecasts:
            raise HTTPException(status_code=500, detail="Forecast generation failed - insufficient data")
        
        return forecasts
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast generation failed: {str(e)}")



@router.get("/validation", response_model=List[ValidationMetrics])
def get_validation_metrics(
    trigger_type: Optional[str] = Query(None, regex="^(drought|flood|crop_failure)$"),
    horizon_months: Optional[int] = Query(None, ge=3, le=6),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get forecast validation metrics
    
    - **trigger_type**: Filter by trigger type
    - **horizon_months**: Filter by forecast horizon
    - **start_date**: Filter by validation date start
    - **end_date**: Filter by validation date end
    
    Returns accuracy metrics including precision, recall, and Brier score.
    """
    try:
        metrics = forecast_service.calculate_validation_metrics(
            db=db,
            trigger_type=trigger_type,
            horizon_months=horizon_months,
            start_date=start_date,
            end_date=end_date
        )
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate validation metrics: {str(e)}")


@router.post("/validation/{target_date}")
def validate_forecasts_for_date(
    target_date: date,
    trigger_type: Optional[str] = Query(None, regex="^(drought|flood|crop_failure)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate forecasts for a specific target date
    
    - **target_date**: Date to validate forecasts for
    - **trigger_type**: Optional filter by trigger type
    
    Compares forecasts against actual trigger events and calculates accuracy metrics.
    """
    try:
        validations = forecast_service.validate_forecasts_for_date(
            db=db,
            target_date=target_date,
            trigger_type=trigger_type
        )
        
        return {
            "target_date": target_date,
            "validations_created": len(validations),
            "message": f"Successfully validated {len(validations)} forecasts"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast validation failed: {str(e)}")



@router.post("/scheduler/run")
def run_forecast_scheduler(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger the forecast scheduler
    
    Runs the automated forecast generation job, which will:
    - Check if forecasts need updating
    - Generate new forecasts if needed
    - Create recommendations for high-probability events
    
    Returns execution summary with status and metrics.
    """
    from app.services.forecast_scheduler import run_forecast_job
    
    try:
        result = run_forecast_job(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scheduler execution failed: {str(e)}")


@router.get("/scheduler/status")
def get_scheduler_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get forecast scheduler status
    
    Returns information about:
    - Latest forecast generation time
    - Whether forecasts need updating
    - Next scheduled run time
    """
    from app.services.forecast_scheduler import ForecastScheduler
    
    try:
        scheduler = ForecastScheduler(db)
        should_run = scheduler.should_run_forecast()
        next_run = scheduler.get_next_run_time()
        
        # Get latest forecast info
        latest_forecast = db.query(Forecast).order_by(
            Forecast.created_at.desc()
        ).first()
        
        return {
            "should_run": should_run,
            "next_run_time": next_run.isoformat() if next_run else None,
            "latest_forecast_date": latest_forecast.forecast_date.isoformat() if latest_forecast else None,
            "latest_forecast_created": latest_forecast.created_at.isoformat() if latest_forecast else None,
            "total_forecasts": db.query(Forecast).count()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")
