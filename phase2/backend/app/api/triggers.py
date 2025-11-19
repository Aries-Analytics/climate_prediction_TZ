from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.schemas.trigger_event import (
    TriggerEventResponse,
    TriggerForecast,
    EarlyWarning,
    TimelineEvent
)
from app.services import trigger_service
from app.models.user import User

router = APIRouter(prefix="/triggers", tags=["triggers"])

@router.get("", response_model=List[TriggerEventResponse])
def list_triggers(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    trigger_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List trigger events with optional filters and pagination"""
    return trigger_service.get_trigger_events(
        db,
        start_date=start_date,
        end_date=end_date,
        trigger_type=trigger_type,
        skip=skip,
        limit=limit
    )

@router.get("/timeline", response_model=List[TimelineEvent])
def get_timeline(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get timeline view of trigger events"""
    return trigger_service.get_trigger_timeline(db, start_date, end_date)

@router.get("/forecast", response_model=List[TriggerForecast])
def get_forecasts(
    months_ahead: int = Query(3, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get trigger probability forecasts"""
    return trigger_service.forecast_trigger_probabilities(db, months_ahead)

@router.get("/warnings", response_model=List[EarlyWarning])
def get_early_warnings(
    threshold: float = Query(0.7, ge=0, le=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get early warning alerts"""
    return trigger_service.generate_early_warnings(db, threshold)

@router.get("/export")
def export_triggers(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    trigger_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export trigger events as CSV"""
    csv_data = trigger_service.export_triggers_csv(
        db,
        start_date=start_date,
        end_date=end_date,
        trigger_type=trigger_type
    )
    
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=trigger_events.csv"
        }
    )

@router.get("/statistics")
def get_statistics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get trigger event statistics"""
    return trigger_service.get_trigger_statistics(db, start_date, end_date)
