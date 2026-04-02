from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from pydantic import BaseModel
from datetime import date

from app.core.database import get_db
from app.models.climate_forecast import ClimateForecast
from app.models.trigger_alert import TriggerAlert
from app.config.rice_thresholds import RAINFALL_THRESHOLDS, get_kilombero_stage

router = APIRouter(prefix="/climate-forecasts", tags=["climate-forecasts"])

# --- schemas ---

class TriggerAlertResponse(BaseModel):
    id: int
    alert_type: str
    severity: str
    phenology_stage: str
    alert_date: date
    location_name: Optional[str] = None
    threshold_value: float
    forecast_value: float
    deviation: Optional[float]
    recommended_action: Optional[str]
    urgency_days: Optional[int]
    location_id: Optional[int] = None
    history: List[float] = []
    
    class Config:
        from_attributes = True

class ClimateForecastResponse(BaseModel):
    id: int
    location_id: int
    forecast_date: date
    target_date: date
    horizon_days: int
    rainfall_mm: Optional[float]
    rainfall_lower: Optional[float]
    rainfall_upper: Optional[float]
    ndvi_value: Optional[float]
    soil_moisture_pct: Optional[float]
    season: Optional[str]
    trigger_alerts: List[TriggerAlertResponse] = []
    
    # Dynamic Thresholds for UI
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    stage_name: Optional[str] = None

    class Config:
        from_attributes = True

# --- endpoints ---

@router.get("/", response_model=List[ClimateForecastResponse])
def get_climate_forecasts(
    location_id: int,
    start_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get climate forecasts for a specific location.
    Useful for plotting rainfall charts.
    """
    query = db.query(ClimateForecast).filter(ClimateForecast.location_id == location_id)
    
    if start_date:
        query = query.filter(ClimateForecast.target_date >= start_date)
        
    # Order by target date to make charting easy
    forecasts = query.order_by(ClimateForecast.target_date).all()
    
    results = []
    for f in forecasts:
        # Convert to Pydantic model
        resp = ClimateForecastResponse.model_validate(f)
        
        # Calculate Thresholds for this date
        season_type = 'dry' if f.season == 'dry_season' else 'wet'
        stage = get_kilombero_stage(f.target_date, season_type)
        resp.stage_name = stage
        
        if stage in RAINFALL_THRESHOLDS:
            resp.threshold_min = RAINFALL_THRESHOLDS[stage].get('min')
            resp.threshold_max = RAINFALL_THRESHOLDS[stage].get('excessive')
            
        results.append(resp)
        
    return results

@router.get("/alerts", response_model=List[TriggerAlertResponse])
def get_active_alerts(
    location_id: Optional[int] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get active insurance triggers/alerts based on High-Confidence Forecasts.
    Sources data from 'Broadcasts' to ensure consistency with Portfolio Risk.
    """
    from app.models.forecast import Forecast, ForecastRecommendation
    from app.models.climate_data import ClimateData
    from app.models.location import Location
    from sqlalchemy import func
    from datetime import timedelta
    
    # Query Forecast directly (Source of Truth for Portfolio Risk)
    # PRIMARY TIER ONLY (horizon_months <= 4): these are insurance-trigger eligible.
    # Advisory tier (5-6 months) is early warning — excluded from payout alerts.
    query = db.query(Forecast).filter(
        Forecast.target_date >= date.today(),
        Forecast.probability >= 0.75,  # High confidence threshold
        Forecast.horizon_months <= 4   # Primary tier only
    )
    
    # PILOT RESTRICTION: Default to Morogoro if no location specified
    # The user requested to only display data from the pilot location for the purpose of the pilot.
    if not location_id:
        morogoro = db.query(Location).filter(Location.name == "Morogoro").first()
        if morogoro:
            query = query.filter(Forecast.location_id == morogoro.id)
    
    if location_id:
        query = query.filter(Forecast.location_id == location_id)
        
    forecasts = query.all()
    
    alerts = []
    today = date.today()
    
    for f in forecasts:
        # Map Forecast to TriggerAlertResponse
        # Determine severity based on probability
        prob = float(f.probability)
        sev = 'critical' if prob >= 0.9 else 'warning'
        
        if severity and severity != sev:
            continue
            
        # Map trigger type names if needed (backend uses snake_case usually)
        t_type = f.trigger_type
        
        # Get recommendation if available
        rec_text = "Monitor conditions."
        if f.recommendations:
            # Get highest priority recommendation
            for rec in f.recommendations:
                if rec.priority == 'high':
                    rec_text = rec.recommendation_text
                    break
            if rec_text == "Monitor conditions." and f.recommendations:
                 rec_text = f.recommendations[0].recommendation_text

        # Calculate urgency
        days_to_impact = (f.target_date - today).days
        
        # Query ClimateForecasts for detailed mm values
        # Optimization: Could fetch all relevant CFs in one query, but loop is okay for small N
        cf = db.query(ClimateForecast).filter(
            ClimateForecast.location_id == f.location_id,
            ClimateForecast.target_date == f.target_date
        ).first()

        # Get Location Name
        loc_name = "Unknown"
        if f.location_id:
             loc_obj = db.query(Location).filter(Location.id == f.location_id).first()
             if loc_obj:
                 loc_name = loc_obj.name

        forecast_val = cf.rainfall_mm if cf else 0.0
        
        # Determine Stage and Threshold
        stage = get_kilombero_stage(f.target_date)

        # Wet-season pilot only covers Jan–Jun. July–Dec is off_season for the main season.
        # Off-season forecasts have no insured crop in the field → no meaningful threshold → exclude.
        if stage == 'off_season':
            continue

        threshold_val = 0.0

        if t_type == "drought":
            threshold_val = RAINFALL_THRESHOLDS.get(stage, {}).get("min", 0.0)
        elif t_type == "flood":
            threshold_val = RAINFALL_THRESHOLDS.get(stage, {}).get("excessive", 0.0)
        
        # Fetch historical data (last 3 months / 90 days) for sparkline
        history_start = today - timedelta(days=90)
        
        location_obj = db.query(Location).filter(Location.id == f.location_id).first()
        history_vals = []
        if location_obj:
            # Query ClimateData using coordinates (exact match as per loader)
            # Use small epsilon if needed, but loader uses exact dict values
            hist_data = db.query(ClimateData.rainfall_mm).filter(
                ClimateData.location_lat == location_obj.latitude,
                ClimateData.location_lon == location_obj.longitude,
                ClimateData.date >= history_start,
                ClimateData.date < today
            ).order_by(ClimateData.date).all()
            
            # Extract values, handle None
            history_vals = [h[0] for h in hist_data if h[0] is not None]
        
        # Fallback to ClimateForecast if ClimateData is empty (rare case or mismatch)
        if not history_vals:
            past_forecasts = db.query(ClimateForecast.rainfall_mm).filter(
                ClimateForecast.location_id == f.location_id,
                ClimateForecast.target_date >= history_start,
                ClimateForecast.target_date < today
            ).order_by(ClimateForecast.target_date).limit(20).all()
            history_vals = [pf[0] for pf in past_forecasts if pf[0] is not None]
        
        # Create response object
        # Note: 'id' here is fake (using forecast id) as we are mapping dynamically
        alert = TriggerAlertResponse(
            id=f.id,
            alert_type=t_type,
            severity=sev,
            phenology_stage=stage,
            alert_date=f.target_date,
            location_name=loc_name,
            threshold_value=threshold_val,
            forecast_value=forecast_val,  
            deviation=float(forecast_val) - threshold_val, # Allow negative values even if cf missing (0 - threshold)
            recommended_action=rec_text,
            urgency_days=days_to_impact,
            location_id=f.location_id,
            history=history_vals
        )
        alerts.append(alert)

    # Sort: Critical first, then by urgency (soonest first)
    alerts.sort(key=lambda x: (0 if x.severity == 'critical' else 1, x.urgency_days))
    
    return alerts
