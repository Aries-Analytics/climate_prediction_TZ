from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import date, datetime, timedelta
from typing import List
from app.models.trigger_event import TriggerEvent
from app.schemas.dashboard import (
    ExecutiveKPIs,
    TriggerRate,
    LossRatioTrend,
    TrendPoint,
    SustainabilityStatus
)

# Configuration constants
TRIGGER_TARGETS = {
    "flood": {"min": 0.05, "max": 0.15},
    "drought": {"min": 0.08, "max": 0.20},
    "crop_failure": {"min": 0.03, "max": 0.12}
}
LOSS_RATIO_THRESHOLD = 0.70
TOTAL_PREMIUMS_YTD = 1000000.0  # This should come from config or database

def calculate_trigger_rate(
    db: Session,
    trigger_type: str,
    start_date: date,
    end_date: date
) -> TriggerRate:
    """Calculate trigger rate for a specific type"""
    # Count triggers
    count = db.query(TriggerEvent).filter(
        TriggerEvent.trigger_type == trigger_type,
        TriggerEvent.date >= start_date,
        TriggerEvent.date <= end_date
    ).count()
    
    # Calculate total days
    total_days = (end_date - start_date).days + 1
    
    # Calculate rate (triggers per day)
    rate = count / total_days if total_days > 0 else 0.0
    
    # Get targets
    targets = TRIGGER_TARGETS.get(trigger_type, {"min": 0.0, "max": 1.0})
    
    # Determine status
    if rate < targets["min"]:
        status = "below_target"
    elif rate > targets["max"]:
        status = "above_target"
    else:
        status = "within_target"
    
    return TriggerRate(
        trigger_type=trigger_type,
        rate=rate,
        count=count,
        target_min=targets["min"],
        target_max=targets["max"],
        status=status
    )

def get_executive_kpis(db: Session) -> ExecutiveKPIs:
    """Get executive dashboard KPIs"""
    # Calculate year-to-date period
    today = date.today()
    start_of_year = date(today.year, 1, 1)
    
    # Calculate trigger rates for each type
    flood_rate = calculate_trigger_rate(db, "flood", start_of_year, today)
    drought_rate = calculate_trigger_rate(db, "drought", start_of_year, today)
    crop_failure_rate = calculate_trigger_rate(db, "crop_failure", start_of_year, today)
    
    # Calculate combined trigger rate
    total_triggers = flood_rate.count + drought_rate.count + crop_failure_rate.count
    total_days = (today - start_of_year).days + 1
    combined_rate = total_triggers / total_days if total_days > 0 else 0.0
    
    # Calculate total payouts YTD
    total_payouts = db.query(func.sum(TriggerEvent.payout_amount)).filter(
        TriggerEvent.date >= start_of_year,
        TriggerEvent.date <= today
    ).scalar() or 0.0
    
    # Calculate loss ratio
    loss_ratio = float(total_payouts) / TOTAL_PREMIUMS_YTD if TOTAL_PREMIUMS_YTD > 0 else 0.0
    
    # Determine sustainability status
    if loss_ratio <= LOSS_RATIO_THRESHOLD:
        sustainability_status = "sustainable"
    elif loss_ratio <= LOSS_RATIO_THRESHOLD * 1.2:
        sustainability_status = "warning"
    else:
        sustainability_status = "unsustainable"
    
    return ExecutiveKPIs(
        flood_trigger_rate=flood_rate,
        drought_trigger_rate=drought_rate,
        crop_failure_trigger_rate=crop_failure_rate,
        combined_trigger_rate=combined_rate,
        loss_ratio=loss_ratio,
        sustainability_status=sustainability_status,
        total_triggers_ytd=total_triggers,
        estimated_payouts_ytd=float(total_payouts)
    )

def get_loss_ratio_trend(db: Session, months: int = 12) -> LossRatioTrend:
    """Get loss ratio trend for the past N months"""
    today = date.today()
    start_date = today - timedelta(days=months * 30)
    
    # Query monthly payouts using strftime for SQLite compatibility
    monthly_data = db.query(
        func.strftime('%Y-%m', TriggerEvent.date).label('month'),
        func.sum(TriggerEvent.payout_amount).label('total_payout')
    ).filter(
        TriggerEvent.date >= start_date,
        TriggerEvent.date <= today
    ).group_by(func.strftime('%Y-%m', TriggerEvent.date)).order_by('month').all()
    
    # Calculate monthly loss ratios
    monthly_premium = TOTAL_PREMIUMS_YTD / 12  # Assume even distribution
    trend_data = []
    
    for month_str, total_payout in monthly_data:
        # Convert month string to date (first day of month)
        year, month = map(int, month_str.split('-'))
        month_date = date(year, month, 1)
        
        loss_ratio = float(total_payout or 0) / monthly_premium if monthly_premium > 0 else 0.0
        trend_data.append(TrendPoint(
            date=month_date,
            value=loss_ratio
        ))
    
    return LossRatioTrend(
        data=trend_data,
        target_threshold=LOSS_RATIO_THRESHOLD
    )

def get_sustainability_status(db: Session) -> SustainabilityStatus:
    """Get current sustainability status with details"""
    kpis = get_executive_kpis(db)
    
    if kpis.sustainability_status == "sustainable":
        message = "System is operating within sustainable parameters"
    elif kpis.sustainability_status == "warning":
        message = "Loss ratio approaching threshold - monitor closely"
    else:
        message = "Loss ratio exceeds threshold - immediate action required"
    
    return SustainabilityStatus(
        status=kpis.sustainability_status,
        loss_ratio=kpis.loss_ratio,
        threshold=LOSS_RATIO_THRESHOLD,
        message=message
    )
