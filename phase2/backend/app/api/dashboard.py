from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.schemas.dashboard import ExecutiveKPIs, LossRatioTrend, SustainabilityStatus
from app.services import dashboard_service
from app.models.user import User
from app.core.cache import cache_manager

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/executive", response_model=ExecutiveKPIs)
async def get_executive_dashboard(
    year: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get executive dashboard KPIs for a specific year (cached for 5 minutes)"""
    cache_key = cache_manager.generate_cache_key("dashboard:executive", year=year)
    
    # Try to get from cache
    cached_data = await cache_manager.get(cache_key)
    if cached_data:
        return cached_data
    
    # Get fresh data
    result = dashboard_service.get_executive_kpis(db, year=year)
    
    # Cache the result
    await cache_manager.set(cache_key, result, ttl=300)  # 5 minutes
    
    return result

@router.get("/triggers/trend", response_model=LossRatioTrend)
async def get_trigger_trend(
    months: int = 12,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get loss ratio trend for the past N months (cached)"""
    cache_key = cache_manager.generate_cache_key("dashboard:trend", months=months)
    
    # Try to get from cache
    cached_data = await cache_manager.get(cache_key)
    if cached_data:
        return cached_data
    
    # Get fresh data
    result = dashboard_service.get_loss_ratio_trend(db, months)
    
    # Cache the result
    await cache_manager.set(cache_key, result, ttl=300)  # 5 minutes
    
    return result

@router.get("/sustainability", response_model=SustainabilityStatus)
async def get_sustainability(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get sustainability status (cached)"""
    cache_key = cache_manager.generate_cache_key("dashboard:sustainability")
    
    # Try to get from cache
    cached_data = await cache_manager.get(cache_key)
    if cached_data:
        return cached_data
    
    # Get fresh data
    result = dashboard_service.get_sustainability_status(db)
    
    # Cache the result
    await cache_manager.set(cache_key, result, ttl=300)  # 5 minutes
    
    return result

@router.get("/years")
async def get_available_years(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of years that have data available (cached for 1 hour)"""
    cache_key = cache_manager.generate_cache_key("dashboard:years")
    
    # Try to get from cache
    cached_data = await cache_manager.get(cache_key)
    if cached_data:
        return cached_data
    
    # Get fresh data
    years = dashboard_service.get_available_years(db)
    result = {"years": years}
    
    # Cache the result for longer since years don't change often
    await cache_manager.set(cache_key, result, ttl=3600)  # 1 hour
    
    return result
