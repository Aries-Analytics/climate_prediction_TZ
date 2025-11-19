from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.schemas.dashboard import ExecutiveKPIs, LossRatioTrend, SustainabilityStatus
from app.services import dashboard_service
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/executive", response_model=ExecutiveKPIs)
def get_executive_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get executive dashboard KPIs"""
    return dashboard_service.get_executive_kpis(db)

@router.get("/triggers/trend", response_model=LossRatioTrend)
def get_trigger_trend(
    months: int = 12,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get loss ratio trend for the past N months"""
    return dashboard_service.get_loss_ratio_trend(db, months)

@router.get("/sustainability", response_model=SustainabilityStatus)
def get_sustainability(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get sustainability status"""
    return dashboard_service.get_sustainability_status(db)
