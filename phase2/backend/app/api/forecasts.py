from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import calendar

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.forecast import Forecast
from app.models.location import Location
from app.schemas.forecast import (
    ForecastResponse,
    ForecastWithRecommendations,
    ForecastGenerateRequest,
    ValidationMetrics,
    LocationRiskSummary,
    LocationRiskSummaryResponse
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
    location_id: Optional[int] = Query(None),  # Morogoro pilot filter
    days: Optional[int] = Query(None),  # Time period filter
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
    - **location_id**: Filter by location (6 = Morogoro pilot)
    - **days**: Filter forecasts within N days from today
    
    Returns list of forecasts matching the criteria.
    """
    try:
        forecasts = forecast_service.get_forecasts(
            db=db,
            trigger_type=trigger_type,
            min_probability=min_probability,
            horizon_months=horizon_months,
            start_date=start_date,
            end_date=end_date,
            location_id=location_id,
            days=days
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
        forecasts = forecast_service.generate_forecasts_all_locations(
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


@router.get("/portfolio-risk")
def get_portfolio_risk(
    days: int = Query(30, ge=1, le=180),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get portfolio risk metrics based on forecasts for the next N days
    
    - **days**: Number of days ahead to calculate risk (default: 30, max: 180)
    
    Returns:
    - farmers_at_risk: Number of farmers with high-risk forecasts (>30%)
    - total_farmers: Total farmers in portfolio (hardcoded for pilot: 500)
    - expected_payouts: Total expected payouts in USD
    - by_trigger_type: Breakdown by drought/flood/crop_failure
    - reserves: Current cash reserves (from config)
    - buffer_percentage: Percentage of reserves remaining after expected payouts
    """
    try:
        # ===== MOROGORO RICE PILOT CONFIGURATION =====
        # Single-location pilot focused on Morogoro (Location ID 6)
        # System continues to generate forecasts for all 6 locations,
        # but pilot calculations filter for Morogoro only
        
        PILOT_LOCATION_ID = 6  # Morogoro, Tanzania
        PILOT_LOCATION_NAME = "Morogoro"
        
        # Parametric insurance payout rates (from PARAMETRIC_INSURANCE_FINAL.md)
        PAYOUT_RATES = {
            "drought": 60,
            "flood": 75,
            "crop_failure": 90
        }
        
        # Portfolio configuration (Morogoro Rice Pilot)
        # Target: 1,000 smallholder rice farmers in Kilombero Basin, Morogoro
        TOTAL_FARMERS = 1000  # Morogoro pilot only
        FARMERS_PER_LOCATION = 1000  # All 1,000 farmers at single pilot location
        CURRENT_RESERVES = 150000  # USD - Updated to meet 100% Capital Adequacy Ratio requirement
        
        # ===== 4-TIER EARLY WARNING THRESHOLD SYSTEM =====
        # Based on industry best practices (ARC, ACRE Africa, parametric insurance standards)
        # See: docs/references/THRESHOLD_ANALYSIS_INDUSTRY_RESEARCH.md
        
        MONITORING_THRESHOLD = 0.30   # 30% - Internal monitoring only, no farmer alerts
        ADVISORY_THRESHOLD = 0.50     # 50% - Send advisory to farmers ("prepare contingency plans")
        WARNING_THRESHOLD = 0.65      # 65% - Send warning to farmers ("implement preventive measures")
        HIGH_RISK_THRESHOLD = 0.75    # 75% - Portfolio risk calculations, payout preparations
        
        # Legacy support (deprecated - use specific thresholds above)
        ALERT_THRESHOLD = ADVISORY_THRESHOLD  # Backwards compatibility
        
        # Calculate target date range
        today = date.today()
        target_end = today + timedelta(days=days)
        
        # Get high-risk forecasts (probability > 0.75) within timeframe
        # **PILOT FILTER**: Only Morogoro (location_id = 6)
        # Threshold raised to 0.75 (75%) to align with "severe event" triggers (1-in-4 year events or worse)
        high_risk_forecasts = db.query(Forecast).filter(
            Forecast.location_id == PILOT_LOCATION_ID,  # ← MOROGORO PILOT FILTER
            Forecast.probability >= 0.75,
            Forecast.target_date >= today,
            Forecast.target_date <= target_end,
            Forecast.horizon_months <= 4  # PRIMARY TIER ONLY — advisory (5-6mo) never triggers payout
        ).all()
        
        # Group forecasts by location to calculate granular risk
        # (For pilot, this will only have 1 location: Morogoro)
        location_risks = {}
        
        for forecast in high_risk_forecasts:
            lid = forecast.location_id
            if lid not in location_risks:
                location_risks[lid] = {}
            
            # Store max probability for this trigger at this location (in case of multiple forecasts)
            current = location_risks[lid].get(forecast.trigger_type, 0)
            # Forecast.probability is Numeric (Decimal), need to float for math
            location_risks[lid][forecast.trigger_type] = max(current, float(forecast.probability))

        # Calculate farmers at risk
        # For single-location pilot: either 0 (no risk) or 1,000 (risk detected)
        farmers_at_risk = len(location_risks) * FARMERS_PER_LOCATION
        
        # Calculate expected payouts and breakdown
        total_expected_payout = 0
        by_trigger_data = {
            "drought": {"count": 0, "payout": 0.0},
            "flood": {"count": 0, "payout": 0.0},
            "crop_failure": {"count": 0, "payout": 0.0}
        }

        for lid, triggers in location_risks.items():
            for trigger_type, prob in triggers.items():
                if trigger_type in by_trigger_data:
                    # Add headcount: 1,000 farmers affected by this trigger
                    by_trigger_data[trigger_type]["count"] += FARMERS_PER_LOCATION
                    
                    # Calculate granular payout derived from this location's specific probability
                    payout = FARMERS_PER_LOCATION * PAYOUT_RATES.get(trigger_type, 0) * prob
                    
                    by_trigger_data[trigger_type]["payout"] += payout
                    total_expected_payout += payout

        # Format by_trigger for response
        by_trigger = {
            k: {"count": v["count"], "payout": round(v["payout"], 2)}
            for k, v in by_trigger_data.items()
        }
        
        # Calculate buffer
        buffer_percentage = ((CURRENT_RESERVES - total_expected_payout) / CURRENT_RESERVES * 100) if CURRENT_RESERVES > 0 else 0
        
        return {
            "farmers_at_risk": farmers_at_risk,
            "total_farmers": TOTAL_FARMERS,
            "risk_percentage": round(farmers_at_risk / TOTAL_FARMERS * 100, 1) if TOTAL_FARMERS > 0 else 0,
            "expected_payouts": round(total_expected_payout, 2),
            "by_trigger_type": by_trigger,
            "reserves": CURRENT_RESERVES,
            "buffer_percentage": round(buffer_percentage, 1),
            "timeframe_days": days,
            "pilot_location_id": PILOT_LOCATION_ID,  # Added for transparency
            "pilot_location_name": PILOT_LOCATION_NAME  # Added for UI display
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate portfolio risk: {str(e)}")


@router.get("/financial-impact")
def get_financial_impact(
    months: int = Query(6, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get projected financial impact based on Climate Forecast Alerts
    Aligned with get_portfolio_risk logic (Threshold > 0.75)
    **PILOT FILTER**: Morogoro location only (ID 6)
    """
    try:
        PILOT_LOCATION_ID = 6  # Morogoro pilot
        
        PAYOUT_RATES = {
            "drought": 60,
            "flood": 75,
            "crop_failure": 90
        }
        
        FARMERS_PER_LOCATION = 1000  # Morogoro rice pilot
        
        today = date.today()
        monthly_projections = []
        
        for month_offset in range(months):
            month_start = today + relativedelta(months=month_offset)
            month_end = month_start + relativedelta(months=1) - timedelta(days=1)
            
            # Query Forecasts directly with same high-risk threshold as portfolio_risk
            # **PILOT FILTER**: Only Morogoro forecasts
            forecasts = db.query(Forecast).filter(
                Forecast.location_id == PILOT_LOCATION_ID,  # ← MOROGORO PILOT FILTER
                Forecast.target_date >= month_start,
                Forecast.target_date <= month_end,
                Forecast.probability >= 0.75
            ).all()
            
            # Group by location/trigger to avoid double-counting within the same month
            # (Use max probability if multiple forecasts exist for same location/trigger in this month)
            location_risks = {}
            
            for f in forecasts:
                # Map trigger types if necessary, though Forecast usually has standard types
                trigger_type = f.trigger_type
                # Handle potential mapping differences if legacy data exists
                if trigger_type == "rainfall_deficit": trigger_type = "drought"
                if trigger_type == "excessive_rainfall": trigger_type = "flood"
                if trigger_type == "ndvi_anomaly": trigger_type = "crop_failure"

                prob = float(f.probability)
                
                key = (f.location_id, trigger_type)
                if key not in location_risks:
                    location_risks[key] = prob
                else:
                    location_risks[key] = max(location_risks[key], prob)
            
            # Calculate expected payouts for this month
            drought_payout = 0
            flood_payout = 0
            crop_payout = 0
            
            for (lid, category), prob in location_risks.items():
                expected_payout = FARMERS_PER_LOCATION * PAYOUT_RATES.get(category, 0) * prob
                
                if category == "drought":
                    drought_payout += expected_payout
                elif category == "flood":
                    flood_payout += expected_payout
                elif category == "crop_failure":
                    crop_payout += expected_payout
            
            monthly_projections.append({
                "month": month_start.strftime("%Y-%m"),
                "month_name": calendar.month_name[month_start.month],
                "drought_payout": round(drought_payout, 2),
                "flood_payout": round(flood_payout, 2),
                "crop_payout": round(crop_payout, 2),
                "total": round(drought_payout + flood_payout + crop_payout, 2)
            })
        
        # Calculate cumulative total
        cumulative = 0
        for projection in monthly_projections:
            cumulative += projection["total"]
            projection["cumulative"] = round(cumulative, 2)
        
        return {
            "projections": monthly_projections,
            "total_exposure": round(cumulative, 2),
            "months": months
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate financial impact: {str(e)}")


@router.get("/location-risk-summary", response_model=LocationRiskSummaryResponse)
def get_location_risk_summary(
    horizon_months: int = Query(3, ge=3, le=6),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get risk summary aggregated by location based on Climate Forecasts
    Aligned with Portfolio Risk logic (Threshold >= 0.75)
    **PILOT FILTER**: Returns only Morogoro (Location ID 6) for single-location pilot
    """
    try:
        PILOT_LOCATION_ID = 6  # Morogoro pilot
        
        # Get only pilot location
        locations = db.query(Location).filter(Location.id == PILOT_LOCATION_ID).all()
        
        location_risks = []
        
        today = date.today()
        target_end = today + relativedelta(months=horizon_months)
        
        # Fetch forecasts directly with high-risk threshold
        # **PILOT FILTER**: Only Morogoro forecasts
        forecasts = db.query(Forecast).filter(
            Forecast.location_id == PILOT_LOCATION_ID,  # ← MOROGORO PILOT FILTER
            Forecast.target_date >= today,
            Forecast.target_date <= target_end,
            Forecast.probability >= 0.75
        ).all()
        
        # Group metrics by Location
        loc_metrics = {} # loc_id -> {drought_max: 0, flood_max: 0, crop_max: 0}
        
        for f in forecasts:
            lid = f.location_id
            if lid not in loc_metrics:
                loc_metrics[lid] = {"drought": 0, "flood": 0, "crop_failure": 0}
            
            prob = float(f.probability)
            
            # Map trigger types clearly
            t_type = f.trigger_type
            if t_type == "rainfall_deficit": t_type = "drought"
            if t_type == "excessive_rainfall": t_type = "flood"
            if t_type == "ndvi_anomaly": t_type = "crop_failure"

            if t_type == "drought":
                loc_metrics[lid]["drought"] = max(loc_metrics[lid]["drought"], prob)
            elif t_type == "flood":
                loc_metrics[lid]["flood"] = max(loc_metrics[lid]["flood"], prob)
            elif t_type == "crop_failure":
                loc_metrics[lid]["crop_failure"] = max(loc_metrics[lid]["crop_failure"], prob)
        
        for location in locations:
            metrics = loc_metrics.get(location.id, {"drought": 0, "flood": 0, "crop_failure": 0})
            
            overall_risk = max(metrics["drought"], metrics["flood"], metrics["crop_failure"])
            
            # Risk Level Logic: High > 0.75 (implied since we filter >= 0.75), but let's keep robust logic
            risk_level = "low"
            if overall_risk >= 0.75:
                risk_level = "high"
            elif overall_risk >= 0.4:
                risk_level = "medium"
            
            # Calculate estimated payout (Expected Value)
            # Constants for payout simulation
            FARMERS_PER_LOCATION = 1000  # Morogoro rice pilot (Kilombero Basin)
            PAYOUT_RATES = {"drought": 60, "flood": 75, "crop_failure": 90}
            
            est_payout = (
                (metrics["drought"] * PAYOUT_RATES["drought"]) +
                (metrics["flood"] * PAYOUT_RATES["flood"]) +
                (metrics["crop_failure"] * PAYOUT_RATES["crop_failure"])
            ) * FARMERS_PER_LOCATION
            
            location_risk = LocationRiskSummary(
                location_id=location.id,
                location_name=location.name,
                latitude=float(location.latitude),
                longitude=float(location.longitude),
                drought_probability=round(metrics["drought"], 4),
                flood_probability=round(metrics["flood"], 4),
                crop_failure_probability=round(metrics["crop_failure"], 4),
                overall_risk_index=round(overall_risk, 4),
                risk_level=risk_level,
                estimated_payout=round(est_payout, 2)
            )
            location_risks.append(location_risk)
        
        # Sort by overall risk (highest first)
        location_risks.sort(key=lambda x: x.overall_risk_index, reverse=True)
        
        return LocationRiskSummaryResponse(
            locations=location_risks,
            horizon_months=horizon_months,
            total_locations=len(location_risks)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get location risk summary: {str(e)}")
