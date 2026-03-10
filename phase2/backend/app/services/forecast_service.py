from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from typing import List, Optional, Tuple
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import numpy as np
import pandas as pd
import pickle
import os
from scipy.stats import norm as _norm_dist

from app.models.forecast import Forecast, ForecastRecommendation, ForecastValidation
from app.models.trigger_event import TriggerEvent
from app.models.climate_data import ClimateData
from app.models.climate_forecast import ClimateForecast
from app.config.rice_thresholds import get_kilombero_stage, RAINFALL_THRESHOLDS
from app.schemas.forecast import (
    ForecastCreate,
    ForecastResponse,
    ForecastWithRecommendations,
    RecommendationCreate,
    RecommendationResponse,
    ValidationMetrics
)
from app.core.config import settings
from app.models.location import Location


# ---------------------------------------------------------------------------
# Physical-threshold probability conversion
# ---------------------------------------------------------------------------
# The XGBoost model was trained on z-score normalised rainfall_mm (same units
# as SPI).  We convert its output to a per-trigger probability by asking:
#   "Given our point prediction and known model uncertainty, what is the
#    probability that actual rainfall crosses the Kilombero phase threshold?"
#
# Source for phase thresholds: rice_thresholds.RAINFALL_THRESHOLDS (TARI/FAO)
# Source for Morogoro stats:   master_dataset.csv, 312 Morogoro records 2000-2025
# Source for model RMSE:       outputs/models/latest_training_results.json
#   XGBoost test RMSE = 0.43 z-score units → 0.43 × 77.06 mm ≈ 33 mm
# ---------------------------------------------------------------------------
_MOROGORO_MEAN_MM: float = 79.15
_MOROGORO_STD_MM:  float = 77.06
_MODEL_RMSE_MM:    float = 33.1   # 0.43 z-score × 77.06 mm/z-score


def _raw_to_probability(raw_prediction: float, trigger_type: str, target_date: date) -> float:
    """
    Convert the model's normalised output (z-score ≈ SPI) to a physically
    meaningful trigger probability using Kilombero phase thresholds.

    Args:
        raw_prediction: XGBoost output (z-score normalised rainfall)
        trigger_type:   'drought' | 'flood' | 'crop_failure' | 'heat_stress'
        target_date:    Forecast target month (determines crop phase & threshold)

    Returns:
        Probability in [0, 1]
    """
    # Denormalise model output to actual mm
    predicted_mm = raw_prediction * _MOROGORO_STD_MM + _MOROGORO_MEAN_MM

    # Get Kilombero crop phase for the target month
    season = 'dry' if target_date.month in (7, 8, 9, 10, 11, 12) else 'wet'
    phase = get_kilombero_stage(target_date, season)
    thresholds = RAINFALL_THRESHOLDS.get(phase, RAINFALL_THRESHOLDS['germination'])

    rmse = _MODEL_RMSE_MM

    if trigger_type == 'drought':
        # P(actual_mm < phase.min | predicted_mm)
        threshold = thresholds['min']
        prob = float(_norm_dist.cdf((threshold - predicted_mm) / rmse))

    elif trigger_type == 'flood':
        # P(actual_mm > phase.excessive | predicted_mm)
        threshold = thresholds['excessive']
        prob = float(1.0 - _norm_dist.cdf((threshold - predicted_mm) / rmse))

    elif trigger_type == 'crop_failure':
        # Severe deficit: rainfall < 50% of phase minimum (trigger_thresholds.yaml
        # rainfall_deficit_pct threshold = 50%)
        threshold = thresholds['min'] * 0.5
        prob = float(_norm_dist.cdf((threshold - predicted_mm) / rmse))

    elif trigger_type == 'heat_stress':
        # No direct rainfall threshold for heat.  Proxy: drought conditions
        # drive heat stress in Kilombero (lower rainfall → higher temperature).
        # Scale by 0.6 to reflect lower base rate (~5-8% vs drought ~12%).
        drought_threshold = thresholds['min']
        prob = float(_norm_dist.cdf((drought_threshold - predicted_mm) / rmse)) * 0.6

    else:
        raise ValueError(f"Unknown trigger_type: {trigger_type}")

    prob = max(0.0, min(1.0, prob))
    print(f"   [{trigger_type}] phase={phase} predicted={predicted_mm:.1f}mm "
          f"threshold={'min' if trigger_type in ('drought','crop_failure','heat_stress') else 'excessive'}"
          f"={thresholds.get('min' if trigger_type != 'flood' else 'excessive', '?'):.0f}mm "
          f"→ P={prob:.3f}")
    return prob


class ForecastGenerator:
    """Service for generating climate trigger forecasts"""
    
    def __init__(self):
        self.model = None
        self.model_version = "ensemble_v1"
        
    def load_model(self):
        """Load the best production model using dynamic resolution.
        
        Reads `active_model.json` to determine which model to load.
        This file is written by the training pipeline after each retrain,
        so the serving code always uses the latest best model.
        
        GOTCHA Law #1: If `active_model.json` is missing, fail explicitly.
        GOTCHA Law #6: Feature count is verified at load time.
        """
        import json
        models_dir = os.path.join(settings.OUTPUTS_DIR, "models")
        config_path = os.path.join(models_dir, "active_model.json")
        
        # active_model.json is REQUIRED — no hardcoded fallbacks (GOTCHA Law #1)
        if not os.path.exists(config_path):
            print(f"ERROR: {config_path} not found. "
                  f"Run the training pipeline to generate it. "
                  f"No hardcoded model fallbacks allowed (GOTCHA Law #1).")
            return False
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"ERROR: Failed to read {config_path}: {e}")
            return False
        
        expected_features = config.get('expected_feature_count', 77)
        
        # Shadow run protocol: ONLY the primary model is permitted.
        # Fallbacks are forbidden — a forecast from the wrong model corrupts the evidence pack.
        if 'primary_model' not in config:
            print("ERROR: active_model.json has no primary_model defined. "
                  "Fallback models are forbidden by shadow run protocol.")
            return False

        pm = config['primary_model']
        model_file = pm['filename']
        version = pm.get('version', 'primary')
        expected_n = pm.get('expected_features', expected_features)
        model_path = os.path.join(models_dir, model_file)

        print(f"Loaded model config from {config_path}")

        if not os.path.exists(model_path):
            print(f"ERROR: Primary model file not found: {model_path}. "
                  f"Shadow run cannot proceed without the validated primary model.")
            return False

        try:
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
                self.model_version = version

            # Verify feature alignment (GOTCHA Law #6)
            if hasattr(self.model, 'n_features_in_'):
                n_features = self.model.n_features_in_
                if n_features != expected_n:
                    print(f"ERROR: {model_file} expects {n_features} features but "
                          f"active_model.json declares {expected_n}. Cannot use misaligned model.")
                    self.model = None
                    return False

            print(f"Loaded primary model: {model_file} (version: {version})")
            return True
        except Exception as e:
            print(f"ERROR: Failed to load primary model {model_file}: {e}")
            self.model = None
            return False
    
    def prepare_features(self, db: Session, start_date: date, horizon_months: int, location: Optional[Location] = None) -> Optional[pd.DataFrame]:
        """
        Prepare features for forecast generation
        
        Args:
            db: Database session
            start_date: Starting date for forecast
            horizon_months: Number of months ahead to forecast
            location: Optional location to filter by
            
        Returns:
            DataFrame with features or None if insufficient data
        """
        # 12-month lookback ensures 6+ monthly records are available even when
        # recent ingestion is delayed (e.g. GEE unavailable for CHIRPS/NDVI).
        from dateutil.relativedelta import relativedelta
        lookback_date = (start_date - relativedelta(months=12)).replace(day=1)

        query = db.query(ClimateData).filter(
            and_(
                ClimateData.date >= lookback_date,
                ClimateData.date <= start_date
            )
        )

        if location:
            # ±0.01° tolerance (~1.1 km). The locations table and climate_data
            # rows use slightly different coordinate precision; 0.001° was too
            # tight for Morogoro (actual diff: 0.0039° in longitude).
            query = query.filter(
                and_(
                    ClimateData.location_lat >= float(location.latitude)  - 0.01,
                    ClimateData.location_lat <= float(location.latitude)  + 0.01,
                    ClimateData.location_lon >= float(location.longitude) - 0.01,
                    ClimateData.location_lon <= float(location.longitude) + 0.01,
                )
            )
            
        climate_data = query.order_by(ClimateData.date).all()
        
        # For monthly data: need at least 6 months (6 records)
        # Previously was 30 (assumed daily data)
        if len(climate_data) < 6:
            print(f"   Insufficient data for {location.name if location else 'location'}: "
                  f"found {len(climate_data)} records, need 6+ months")
            return None
        
        print(f"   {location.name if location else 'location'}: Using {len(climate_data)} monthly records "
              f"from {climate_data[0].date} to {climate_data[-1].date}")
        
        # Convert to DataFrame with ALL ClimateData columns (including atmospheric)
        df = pd.DataFrame([{
            'date': cd.date,
            'month': cd.date.month if cd.date else None,
            'temperature': float(cd.temperature_avg) if cd.temperature_avg else None,
            'rainfall': float(cd.rainfall_mm) if cd.rainfall_mm else None,
            'ndvi': float(cd.ndvi) if cd.ndvi else None,
            'soil_moisture': float(cd.soil_moisture) if cd.soil_moisture else None,
            'enso': float(cd.enso_index) if cd.enso_index else None,
            'iod': float(cd.iod_index) if cd.iod_index else None,
            # Atmospheric columns (expanded schema)
            'humidity': float(cd.humidity_pct) if cd.humidity_pct else None,
            'rel_humidity': float(cd.rel_humidity_pct) if cd.rel_humidity_pct else None,
            'dewpoint': float(cd.dewpoint_2m) if cd.dewpoint_2m else None,
            'wind_speed': float(cd.wind_speed_ms) if cd.wind_speed_ms else None,
            'wind_u': float(cd.wind_u_10m) if cd.wind_u_10m else None,
            'wind_v': float(cd.wind_v_10m) if cd.wind_v_10m else None,
            'wind_direction': float(cd.wind_direction_deg) if cd.wind_direction_deg else None,
            'pressure': float(cd.surface_pressure) if cd.surface_pressure else None,
            'solar': float(cd.solar_rad_wm2) if cd.solar_rad_wm2 else None,
            'location_name': location.name if location else 'Unknown',
        } for cd in climate_data])
        
        # Check for critical missing data (GOTCHA Law #1: no synthetic fill)
        # If a data source failed, its columns will be all None.
        # Rather than filling with fake 0s, skip forecast and retry next run.
        critical_columns = ['temperature', 'rainfall']  # Minimum required
        for col in critical_columns:
            if col in df.columns and df[col].isna().all():
                print(f"   SKIPPING {location.name if location else 'location'}: "
                      f"critical column '{col}' is entirely None (data source failed). "
                      f"No fabricated fallbacks (GOTCHA Law #1). Will retry next run.")
                return None
        
        # Use feature_engineering module to build the exact 88 features
        try:
            from app.services.feature_engineering import build_feature_vector
        except ImportError:
            from backend.app.services.feature_engineering import build_feature_vector
        
        features_df = build_feature_vector(df)
        if features_df is None:
            print(f"   Feature engineering failed for {location.name if location else 'location'}")
            return None
        
        print(f"   Generated {features_df.shape[1]} features for prediction")
        return features_df

    def calculate_confidence_intervals(self, probability: float, uncertainty: float = 0.15) -> Tuple[float, float]:
        # ... (keep existing implementation)
        lower = max(0.0, probability - uncertainty)
        upper = min(1.0, probability + uncertainty)
        return lower, upper

    def generate_forecast(
        self,
        db: Session,
        start_date: date,
        horizon_months: int,
        trigger_type: str,
        location: Optional[Location] = None
    ) -> Optional[ForecastCreate]:
        """
        Generate a single forecast
        """
        # Calculate target date
        target_date = start_date + relativedelta(months=horizon_months)
        
        # Prepare features
        features_df = self.prepare_features(db, start_date, horizon_months, location)
        if features_df is None:
            return None
        
        # Generate prediction
        if self.model is not None:
            try:
                # CRITICAL: Use .predict() for regressors, NEVER .predict_proba()
                # Model outputs z-score normalised rainfall (same units as SPI).
                # Convert to trigger probability via physical phase thresholds
                # (rice_thresholds.RAINFALL_THRESHOLDS) + model uncertainty (RMSE).
                raw_prediction = self.model.predict(features_df)[0]
                probability = _raw_to_probability(raw_prediction, trigger_type, target_date)
            except Exception as e:
                print(f"Model prediction failed for {trigger_type}: {e}")
                return None  # GOTCHA Law #1: No fabricated fallbacks
        else:
            # No model loaded — cannot generate forecast
            print(f"  ERROR: No model loaded for {trigger_type} forecast. "
                  f"Load a trained model to resolve.")
            return None  # GOTCHA Law #1: No fabricated fallbacks
        
        # Calculate confidence intervals
        base_uncertainty = 0.15
        horizon_uncertainty = base_uncertainty + (0.02 * (horizon_months - 3))
        confidence_lower, confidence_upper = self.calculate_confidence_intervals(probability, horizon_uncertainty)
        
        return ForecastCreate(
            location_id=location.id if location else None,
            forecast_date=start_date,
            target_date=target_date,
            horizon_months=horizon_months,
            trigger_type=trigger_type,
            probability=probability,
            confidence_lower=confidence_lower,
            confidence_upper=confidence_upper,
            model_version=self.model_version
        )


def generate_forecasts_all_locations(
    db: Session,
    start_date: Optional[date] = None,
    horizons: List[int] = [3, 4, 5, 6]
) -> List[ForecastResponse]:
    """Generate forecasts for all locations"""
    if start_date is None:
        start_date = date.today()
    
    generator = ForecastGenerator()
    generator.load_model()
    
    # Generate for all locations that have climate data
    # Frontend will filter to show only location_id=6 (Morogoro)
    locations = db.query(Location).all()
    
    if not locations:
        print(f"ERROR: No locations found in database!")
        return []
    
    trigger_types = ["drought", "flood", "crop_failure"]
    forecasts = []
    
    print(f"Generating forecasts for {len(locations)} locations: {[l.name for l in locations]}")
    
    for location in locations:
        for trigger_type in trigger_types:
            for horizon in horizons:
                forecast_data = generator.generate_forecast(db, start_date, horizon, trigger_type, location)
                
                if forecast_data:
                    # Update or create
                    existing = db.query(Forecast).filter(
                        and_(
                            Forecast.location_id == location.id,
                            Forecast.forecast_date == forecast_data.forecast_date,
                            Forecast.target_date == forecast_data.target_date,
                            Forecast.trigger_type == forecast_data.trigger_type
                        )
                    ).first()
                    
                    if existing:
                        for key, value in forecast_data.model_dump().items():
                            setattr(existing, key, value)
                        db.commit()
                        db.refresh(existing)
                        forecasts.append(ForecastResponse.model_validate(existing))
                    else:
                        forecast = Forecast(**forecast_data.model_dump())
                        db.add(forecast)
                        db.commit()
                        db.refresh(forecast)
                        forecasts.append(ForecastResponse.model_validate(forecast))
    return forecasts


# Alias for compatibility with orchestrator
generate_forecasts = generate_forecasts_all_locations


def get_latest_forecasts(db: Session) -> List[ForecastResponse]:
    """Get the most recent forecasts for all trigger types and horizons"""
    # Get the latest forecast_date
    latest_date = db.query(func.max(Forecast.forecast_date)).scalar()
    
    if not latest_date:
        return []
    
    forecasts = db.query(Forecast).filter(
        Forecast.forecast_date == latest_date
    ).all()
    
    return [ForecastResponse.model_validate(f) for f in forecasts]


def get_forecasts(
    db: Session,
    trigger_type: Optional[str] = None,
    min_probability: Optional[float] = None,
    horizon_months: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    location_id: Optional[int] = None,
    days: Optional[int] = None
) -> List[ForecastResponse]:
    """
    Query forecasts with filters
    
    Args:
        db: Database session
        trigger_type: Filter by trigger type
        min_probability: Minimum probability threshold
        horizon_months: Filter by horizon
        start_date: Filter by target date start
        end_date: Filter by target date end
        location_id: Filter by location ID (6 = Morogoro)
        days: Filter forecasts within N days from today
        
    Returns:
        List of matching forecasts with staleness flags
    """
    from datetime import datetime, timedelta, timezone
    
    query = db.query(Forecast)
    
    if trigger_type:
        query = query.filter(Forecast.trigger_type == trigger_type)
    
    if min_probability is not None:
        query = query.filter(Forecast.probability >= min_probability)
    
    if horizon_months is not None:
        query = query.filter(Forecast.horizon_months == horizon_months)
    
    if location_id is not None:
        query = query.filter(Forecast.location_id == location_id)
    
    if days is not None:
        from_date = datetime.now(timezone.utc).date()
        to_date = from_date + timedelta(days=days)
        query = query.filter(
            Forecast.target_date >= from_date,
            Forecast.target_date <= to_date
        )
    
    if start_date:
        query = query.filter(Forecast.target_date >= start_date)
    
    if end_date:
        query = query.filter(Forecast.target_date <= end_date)
    
    forecasts = query.order_by(desc(Forecast.target_date)).all()
    
    # Convert to response objects with staleness flag and UI context
    staleness_threshold = timedelta(days=7)
    now = datetime.now(timezone.utc)
    
    result = []
    for f in forecasts:
        forecast_response = ForecastResponse.model_validate(f)
        
        # 1. Staleness
        if f.created_at:
            age = now - f.created_at
            forecast_response.is_stale = age > staleness_threshold
        else:
            forecast_response.is_stale = False
            
        # 2. Phenology Stage — detect season from target month
        season_type = 'dry' if f.target_date.month >= 7 else 'wet'
        stage = get_kilombero_stage(f.target_date, season_type)
        forecast_response.stage = stage
        
        # 3. Threshold Value
        t_type = f.trigger_type
        if t_type == "rainfall_deficit": t_type = "drought"
        if t_type == "excessive_rainfall": t_type = "flood"
        
        threshold = 0.0
        if t_type == 'drought':
             threshold = RAINFALL_THRESHOLDS.get(stage, {}).get('min', 0.0)
        elif t_type == 'flood':
             threshold = RAINFALL_THRESHOLDS.get(stage, {}).get('excessive', 0.0)
        
        forecast_response.threshold_value = threshold
        
        # 4. Expected Deficit / Deviation
        # Only query if meaningful
        if threshold > 0:
            cf = db.query(ClimateForecast).filter(
                and_(
                    ClimateForecast.location_id == f.location_id,
                    ClimateForecast.target_date == f.target_date
                )
            ).first()
            
            if cf:
                forecast_val = float(cf.rainfall_mm or 0.0)
                if t_type == 'drought':
                    # Deficit: Threshold - Actual (e.g. 100 - 80 = 20mm deficit)
                    forecast_response.expected_deficit = max(0.0, threshold - forecast_val)
                elif t_type == 'flood':
                    # Excess: Actual - Threshold (e.g. 300 - 250 = 50mm excess)
                    forecast_response.expected_deficit = max(0.0, forecast_val - threshold)
        
        result.append(forecast_response)
    
    return result



# Recommendation Engine
RECOMMENDATION_TEMPLATES = {
    "drought": {
        "high": {
            "text": "HIGH RISK: Severe drought conditions predicted. Implement water conservation measures immediately. Consider drought-resistant crop varieties and early planting strategies. Prepare irrigation systems and water storage facilities.",
            "timeline": "Immediate action required (within 2 weeks)",
        },
        "medium": {
            "text": "MODERATE RISK: Drought conditions likely. Begin water conservation planning. Review crop selection and consider drought-tolerant varieties. Monitor soil moisture levels closely.",
            "timeline": "Action recommended within 1 month",
        },
        "low": {
            "text": "LOW RISK: Slight drought possibility. Continue normal operations but monitor weather forecasts. Ensure water management systems are functional.",
            "timeline": "Routine monitoring",
        }
    },
    "flood": {
        "high": {
            "text": "HIGH RISK: Severe flooding predicted. Prepare drainage systems and flood barriers. Consider flood-resistant crop varieties. Secure equipment and livestock. Review emergency evacuation plans.",
            "timeline": "Immediate action required (within 2 weeks)",
        },
        "medium": {
            "text": "MODERATE RISK: Flooding conditions likely. Inspect and clear drainage channels. Prepare flood mitigation measures. Consider delaying planting in low-lying areas.",
            "timeline": "Action recommended within 1 month",
        },
        "low": {
            "text": "LOW RISK: Slight flood possibility. Ensure drainage systems are clear. Monitor rainfall forecasts closely.",
            "timeline": "Routine monitoring",
        }
    },
    "crop_failure": {
        "high": {
            "text": "HIGH RISK: Crop failure conditions predicted. Diversify crop portfolio immediately. Consider early harvest of vulnerable crops. Implement pest and disease prevention measures. Review insurance coverage.",
            "timeline": "Immediate action required (within 2 weeks)",
        },
        "medium": {
            "text": "MODERATE RISK: Crop stress conditions likely. Monitor crop health closely. Prepare contingency plans for alternative crops. Ensure adequate pest control measures.",
            "timeline": "Action recommended within 1 month",
        },
        "low": {
            "text": "LOW RISK: Slight crop stress possibility. Continue normal crop management. Monitor for early signs of stress or disease.",
            "timeline": "Routine monitoring",
        }
    }
}


def generate_recommendations(
    db: Session,
    forecast: Forecast,
    threshold: float = 0.3
) -> List[ForecastRecommendation]:
    """
    Generate recommendations for a forecast
    
    Args:
        db: Database session
        forecast: Forecast object
        threshold: Minimum probability to generate recommendations
        
    Returns:
        List of generated recommendations
    """
    recommendations = []
    
    # Only generate recommendations if probability exceeds threshold
    if forecast.probability < threshold:
        return recommendations
    
    # Determine priority based on probability
    if forecast.probability >= 0.6:
        priority = "high"
    elif forecast.probability >= 0.4:
        priority = "medium"
    else:
        priority = "low"
    
    # Get recommendation template
    template = RECOMMENDATION_TEMPLATES.get(forecast.trigger_type, {}).get(priority)
    
    if template:
        recommendation = ForecastRecommendation(
            forecast_id=forecast.id,
            recommendation_text=template["text"],
            priority=priority,
            action_timeline=template["timeline"]
        )
        db.add(recommendation)
        recommendations.append(recommendation)
    
    return recommendations


def generate_all_recommendations(
    db: Session,
    min_probability: float = 0.3
) -> List[RecommendationResponse]:
    """
    Generate recommendations for all high-probability forecasts
    
    Args:
        db: Database session
        min_probability: Minimum probability threshold
        
    Returns:
        List of generated recommendations
    """
    # Get forecasts above threshold without existing recommendations
    forecasts = db.query(Forecast).filter(
        Forecast.probability >= min_probability
    ).all()
    
    all_recommendations = []
    
    for forecast in forecasts:
        # Check if recommendations already exist
        existing = db.query(ForecastRecommendation).filter(
            ForecastRecommendation.forecast_id == forecast.id
        ).first()
        
        if not existing:
            recommendations = generate_recommendations(db, forecast, min_probability)
            all_recommendations.extend(recommendations)
    
    db.commit()
    
    # Refresh and return
    return [RecommendationResponse.model_validate(r) for r in all_recommendations]


def get_recommendations(
    db: Session,
    min_probability: Optional[float] = None,
    trigger_type: Optional[str] = None,
    priority: Optional[str] = None
) -> List[ForecastWithRecommendations]:
    """
    Get forecasts with their recommendations
    
    Args:
        db: Database session
        min_probability: Filter by minimum probability
        trigger_type: Filter by trigger type
        priority: Filter by recommendation priority
        
    Returns:
        List of forecasts with recommendations
    """
    from sqlalchemy.orm import joinedload
    
    query = db.query(Forecast).join(ForecastRecommendation).options(joinedload(Forecast.recommendations))
    
    if min_probability is not None:
        query = query.filter(Forecast.probability >= min_probability)
    
    if trigger_type:
        query = query.filter(Forecast.trigger_type == trigger_type)
    
    if priority:
        query = query.filter(ForecastRecommendation.priority == priority)
    
    forecasts = query.distinct().order_by(desc(Forecast.probability)).all()
    
    return [ForecastWithRecommendations.model_validate(f) for f in forecasts]



# Forecast Validation Service
def validate_forecast(
    db: Session,
    forecast: Forecast,
    actual_trigger: Optional[TriggerEvent] = None
) -> ForecastValidation:
    """
    Validate a forecast against actual outcome
    
    Args:
        db: Database session
        forecast: Forecast to validate
        actual_trigger: Actual trigger event that occurred (None if no trigger)
        
    Returns:
        ForecastValidation object
    """
    # Determine if forecast was correct
    # A forecast is considered correct if:
    # - It predicted high probability (>0.5) and trigger occurred
    # - It predicted low probability (<=0.5) and no trigger occurred
    
    trigger_occurred = actual_trigger is not None
    predicted_trigger = forecast.probability > 0.5
    
    was_correct = (predicted_trigger and trigger_occurred) or (not predicted_trigger and not trigger_occurred)
    
    # Calculate probability error
    # If trigger occurred, error = 1 - probability
    # If no trigger, error = probability
    if trigger_occurred:
        probability_error = 1.0 - float(forecast.probability)
    else:
        probability_error = float(forecast.probability)
    
    # Calculate Brier score
    # Brier score = (probability - actual)^2 where actual is 1 if trigger occurred, 0 otherwise
    actual_value = 1.0 if trigger_occurred else 0.0
    brier_score = (float(forecast.probability) - actual_value) ** 2
    
    # Create validation record
    validation = ForecastValidation(
        forecast_id=forecast.id,
        actual_trigger_id=actual_trigger.id if actual_trigger else None,
        was_correct=1 if was_correct else 0,
        probability_error=probability_error,
        brier_score=brier_score
    )
    
    db.add(validation)
    db.commit()
    db.refresh(validation)
    
    return validation


def validate_forecasts_for_date(
    db: Session,
    target_date: date,
    trigger_type: Optional[str] = None
) -> List[ForecastValidation]:
    """
    Validate all forecasts for a specific target date
    
    Args:
        db: Database session
        target_date: Date to validate forecasts for
        trigger_type: Optional filter by trigger type
        
    Returns:
        List of validation records
    """
    # Get all forecasts for this target date
    query = db.query(Forecast).filter(Forecast.target_date == target_date)
    
    if trigger_type:
        query = query.filter(Forecast.trigger_type == trigger_type)
    
    forecasts = query.all()
    
    validations = []
    
    for forecast in forecasts:
        # Check if validation already exists
        existing = db.query(ForecastValidation).filter(
            ForecastValidation.forecast_id == forecast.id
        ).first()
        
        if existing:
            continue  # Skip if already validated
        
        # Look for actual trigger event
        actual_trigger = db.query(TriggerEvent).filter(
            and_(
                TriggerEvent.trigger_date == target_date,
                TriggerEvent.trigger_type == forecast.trigger_type
            )
        ).first()
        
        # Validate forecast
        validation = validate_forecast(db, forecast, actual_trigger)
        validations.append(validation)
    
    return validations


def calculate_validation_metrics(
    db: Session,
    trigger_type: Optional[str] = None,
    horizon_months: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[ValidationMetrics]:
    """
    Calculate validation metrics for forecasts
    
    Args:
        db: Database session
        trigger_type: Filter by trigger type
        horizon_months: Filter by horizon
        start_date: Filter by validation date start
        end_date: Filter by validation date end
        
    Returns:
        List of validation metrics grouped by trigger type and horizon
    """
    from sqlalchemy import func
    
    # Build query
    query = db.query(
        Forecast.trigger_type,
        Forecast.horizon_months,
        func.count(ForecastValidation.id).label('total_forecasts'),
        func.sum(ForecastValidation.was_correct).label('correct_forecasts'),
        func.avg(ForecastValidation.brier_score).label('avg_brier_score')
    ).join(
        ForecastValidation,
        Forecast.id == ForecastValidation.forecast_id
    )
    
    # Apply filters
    if trigger_type:
        query = query.filter(Forecast.trigger_type == trigger_type)
    
    if horizon_months:
        query = query.filter(Forecast.horizon_months == horizon_months)
    
    if start_date:
        query = query.filter(ForecastValidation.validated_at >= start_date)
    
    if end_date:
        query = query.filter(ForecastValidation.validated_at <= end_date)
    
    # Group by trigger type and horizon
    query = query.group_by(Forecast.trigger_type, Forecast.horizon_months)
    
    results = query.all()
    
    metrics = []
    for result in results:
        total = result.total_forecasts or 0
        correct = result.correct_forecasts or 0
        
        accuracy = (correct / total) if total > 0 else 0.0
        
        # Calculate precision and recall
        # For this, we need to query true positives, false positives, false negatives
        tp_query = db.query(func.count(ForecastValidation.id)).join(Forecast).filter(
            and_(
                Forecast.trigger_type == result.trigger_type,
                Forecast.horizon_months == result.horizon_months,
                Forecast.probability > 0.5,
                ForecastValidation.actual_trigger_id.isnot(None)
            )
        )
        
        fp_query = db.query(func.count(ForecastValidation.id)).join(Forecast).filter(
            and_(
                Forecast.trigger_type == result.trigger_type,
                Forecast.horizon_months == result.horizon_months,
                Forecast.probability > 0.5,
                ForecastValidation.actual_trigger_id.is_(None)
            )
        )
        
        fn_query = db.query(func.count(ForecastValidation.id)).join(Forecast).filter(
            and_(
                Forecast.trigger_type == result.trigger_type,
                Forecast.horizon_months == result.horizon_months,
                Forecast.probability <= 0.5,
                ForecastValidation.actual_trigger_id.isnot(None)
            )
        )
        
        if start_date:
            tp_query = tp_query.filter(ForecastValidation.validated_at >= start_date)
            fp_query = fp_query.filter(ForecastValidation.validated_at >= start_date)
            fn_query = fn_query.filter(ForecastValidation.validated_at >= start_date)
        
        if end_date:
            tp_query = tp_query.filter(ForecastValidation.validated_at <= end_date)
            fp_query = fp_query.filter(ForecastValidation.validated_at <= end_date)
            fn_query = fn_query.filter(ForecastValidation.validated_at <= end_date)
        
        tp = tp_query.scalar() or 0
        fp = fp_query.scalar() or 0
        fn = fn_query.scalar() or 0
        
        precision = (tp / (tp + fp)) if (tp + fp) > 0 else None
        recall = (tp / (tp + fn)) if (tp + fn) > 0 else None
        
        metrics.append(ValidationMetrics(
            trigger_type=result.trigger_type,
            horizon_months=result.horizon_months,
            total_forecasts=total,
            correct_forecasts=correct,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            avg_brier_score=float(result.avg_brier_score) if result.avg_brier_score else None
        ))
    
    return metrics


def check_model_retraining_needed(
    db: Session,
    accuracy_threshold: float = 0.6
) -> List[str]:
    """
    Check if models need retraining based on accuracy
    
    Args:
        db: Database session
        accuracy_threshold: Minimum acceptable accuracy (default 0.6)
        
    Returns:
        List of trigger types that need retraining
    """
    metrics = calculate_validation_metrics(db)
    
    needs_retraining = []
    
    for metric in metrics:
        if metric.accuracy < accuracy_threshold:
            model_key = f"{metric.trigger_type}_{metric.horizon_months}m"
            needs_retraining.append(model_key)
    
    return needs_retraining
