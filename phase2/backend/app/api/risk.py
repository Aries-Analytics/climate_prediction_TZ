from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.services import risk_service
from app.models.user import User

router = APIRouter(prefix="/risk", tags=["risk"])

@router.get("/portfolio")
def get_portfolio(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get portfolio-level risk metrics"""
    return risk_service.get_portfolio_metrics(db)

@router.post("/scenario")
def run_scenario(
    scenario: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Run scenario analysis"""
    return risk_service.run_scenario_analysis(db, scenario)

@router.get("/recommendations")
def get_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get risk management recommendations"""
    return risk_service.get_recommendations(db)
