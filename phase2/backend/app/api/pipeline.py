"""
Pipeline API endpoints for data freshness and status
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.database import get_db
from app.models.climate_data import ClimateData
from app.models.forecast import Forecast
from app.models.pipeline_execution import PipelineExecution

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/freshness")
def get_data_freshness(db: Session = Depends(get_db)):
    """
    Get data freshness metadata for all climate data sources.
    
    Returns timestamps of most recent data for each source and staleness warnings.
    """
    # Get most recent climate data
    latest_climate = db.query(
        func.max(ClimateData.date).label('latest_date'),
        func.max(ClimateData.created_at).label('latest_ingestion')
    ).first()
    
    # Get most recent forecast
    latest_forecast = db.query(
        func.max(Forecast.created_at).label('latest_forecast')
    ).first()
    
    # Get most recent pipeline execution
    latest_execution = db.query(PipelineExecution).order_by(
        desc(PipelineExecution.started_at)
    ).first()
    
    # Calculate staleness
    now = datetime.now(timezone.utc)
    staleness_threshold = timedelta(days=7)
    
    climate_stale = False
    forecast_stale = False
    
    if latest_climate.latest_date:
        climate_age = now.date() - latest_climate.latest_date
        climate_stale = climate_age > staleness_threshold
    
    if latest_forecast.latest_forecast:
        forecast_age = now - latest_forecast.latest_forecast
        forecast_stale = forecast_age > staleness_threshold
    
    # Check if pipeline is currently running
    is_updating = False
    if latest_execution and latest_execution.status == 'running':
        is_updating = True
    
    return {
        "climate_data": {
            "latest_date": latest_climate.latest_date.isoformat() if latest_climate.latest_date else None,
            "latest_ingestion": latest_climate.latest_ingestion.isoformat() if latest_climate.latest_ingestion else None,
            "is_stale": climate_stale,
            "age_days": (now.date() - latest_climate.latest_date).days if latest_climate.latest_date else None
        },
        "forecasts": {
            "latest_generation": latest_forecast.latest_forecast.isoformat() if latest_forecast.latest_forecast else None,
            "is_stale": forecast_stale,
            "age_days": (now - latest_forecast.latest_forecast).days if latest_forecast.latest_forecast else None
        },
        "pipeline": {
            "is_updating": is_updating,
            "last_execution": latest_execution.started_at.isoformat() if latest_execution else None,
            "last_status": latest_execution.status if latest_execution else None
        }
    }


@router.get("/status")
def get_pipeline_status(db: Session = Depends(get_db)):
    """
    Get current pipeline execution status.
    
    Returns current state, progress, and recent execution history.
    """
    # Get current/most recent execution
    latest_execution = db.query(PipelineExecution).order_by(
        desc(PipelineExecution.started_at)
    ).first()
    
    if not latest_execution:
        return {
            "status": "idle",
            "message": "No pipeline executions found"
        }
    
    # Determine current stage based on status
    current_stage = None
    progress_pct = 0
    
    if latest_execution.status == 'running':
        if latest_execution.forecasts_generated and latest_execution.forecasts_generated > 0:
            current_stage = 'forecasting'
            progress_pct = 75
        elif latest_execution.records_stored and latest_execution.records_stored > 0:
            current_stage = 'ingestion'
            progress_pct = 50
        else:
            current_stage = 'starting'
            progress_pct = 10
    elif latest_execution.status in ['completed', 'partial']:
        current_stage = 'completed'
        progress_pct = 100
    elif latest_execution.status == 'failed':
        current_stage = 'failed'
        progress_pct = 0
    
    return {
        "execution_id": latest_execution.id,
        "status": latest_execution.status,
        "current_stage": current_stage,
        "progress_pct": progress_pct,
        "started_at": latest_execution.started_at.isoformat(),
        "completed_at": latest_execution.completed_at.isoformat() if latest_execution.completed_at else None,
        "duration_seconds": latest_execution.duration_seconds,
        "records_fetched": latest_execution.records_fetched,
        "records_stored": latest_execution.records_stored,
        "forecasts_generated": latest_execution.forecasts_generated,
        "sources_succeeded": latest_execution.sources_succeeded or [],
        "sources_failed": latest_execution.sources_failed or [],
        "error_message": latest_execution.error_message
    }
