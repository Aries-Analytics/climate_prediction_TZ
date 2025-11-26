from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from typing import List, Optional, Tuple
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import numpy as np
import pandas as pd
import pickle
import os

from app.models.forecast import Forecast, ForecastRecommendation, ForecastValidation
from app.models.trigger_event import TriggerEvent
from app.models.climate_data import ClimateData
from app.schemas.forecast import (
    ForecastCreate,
    ForecastResponse,
    ForecastWithRecommendations,
    RecommendationCreate,
    RecommendationResponse,
    ValidationMetrics
)
from app.core.config import settings


class ForecastGenerator:
    """Service for generating climate trigger forecasts"""
    
    def __init__(self):
        self.model = None
        self.model_version = "ensemble_v1"
        
    def load_model(self):
        """Load trained model from disk (supports both pickle and Keras formats)"""
        try:
            # Try to load Keras model first (for LSTM)
            keras_path = os.path.join(settings.OUTPUTS_DIR, "models", "best_model.keras")
            if os.path.exists(keras_path):
                try:
                    from tensorflow import keras
                    self.model = keras.models.load_model(keras_path)
                    self.model_version = "lstm_v1"
                    print(f"Loaded Keras model from {keras_path}")
                    return True
                except Exception as e:
                    print(f"Failed to load Keras model: {e}")
            
            # Fall back to pickle format (for RF, XGBoost, Ensemble)
            pkl_path = os.path.join(settings.OUTPUTS_DIR, "models", "best_model.pkl")
            if os.path.exists(pkl_path):
                with open(pkl_path, 'rb') as f:
                    self.model = pickle.load(f)
                    self.model_version = "ensemble_v1"
                    print(f"Loaded pickle model from {pkl_path}")
                return True
        except Exception as e:
            print(f"Failed to load model: {e}")
        return False
    
    def prepare_features(self, db: Session, start_date: date, horizon_months: int) -> Optional[pd.DataFrame]:
        """
        Prepare features for forecast generation
        
        Args:
            db: Database session
            start_date: Starting date for forecast
            horizon_months: Number of months ahead to forecast
            
        Returns:
            DataFrame with features or None if insufficient data
        """
        # Get recent climate data (last 6 months)
        lookback_date = start_date - timedelta(days=180)
        
        climate_data = db.query(ClimateData).filter(
            and_(
                ClimateData.date >= lookback_date,
                ClimateData.date <= start_date
            )
        ).order_by(ClimateData.date).all()
        
        if len(climate_data) < 30:  # Need at least 30 days of data
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': cd.date,
            'temperature': float(cd.temperature_avg) if cd.temperature_avg else None,
            'rainfall': float(cd.rainfall_mm) if cd.rainfall_mm else None,
            'ndvi': float(cd.ndvi) if cd.ndvi else None,
            'enso': float(cd.enso_index) if cd.enso_index else None,
            'iod': float(cd.iod_index) if cd.iod_index else None,
        } for cd in climate_data])
        
        # Calculate aggregate features
        features = {
            'avg_temp_30d': df['temperature'].tail(30).mean(),
            'avg_rainfall_30d': df['rainfall'].tail(30).mean(),
            'avg_ndvi_30d': df['ndvi'].tail(30).mean(),
            'avg_temp_90d': df['temperature'].tail(90).mean(),
            'avg_rainfall_90d': df['rainfall'].tail(90).mean(),
            'total_rainfall_30d': df['rainfall'].tail(30).sum(),
            'total_rainfall_90d': df['rainfall'].tail(90).sum(),
            'enso_latest': df['enso'].iloc[-1] if not df['enso'].isna().all() else 0,
            'iod_latest': df['iod'].iloc[-1] if not df['iod'].isna().all() else 0,
            'horizon_months': horizon_months,
        }
        
        return pd.DataFrame([features])
    
    def calculate_confidence_intervals(
        self, 
        probability: float, 
        uncertainty: float = 0.15
    ) -> Tuple[float, float]:
        """
        Calculate confidence intervals for a probability prediction
        
        Args:
            probability: Base probability (0-1)
            uncertainty: Uncertainty factor (default 0.15)
            
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        lower = max(0.0, probability - uncertainty)
        upper = min(1.0, probability + uncertainty)
        return lower, upper
    
    def generate_forecast(
        self,
        db: Session,
        start_date: date,
        horizon_months: int,
        trigger_type: str
    ) -> Optional[ForecastCreate]:
        """
        Generate a single forecast
        
        Args:
            db: Database session
            start_date: Date to forecast from
            horizon_months: Months ahead (3-6)
            trigger_type: Type of trigger (drought, flood, crop_failure)
            
        Returns:
            ForecastCreate object or None if generation fails
        """
        # Calculate target date
        target_date = start_date + relativedelta(months=horizon_months)
        
        # Prepare features
        features_df = self.prepare_features(db, start_date, horizon_months)
        if features_df is None:
            return None
        
        # Generate prediction
        if self.model is not None:
            try:
                # Use model to predict
                prediction = self.model.predict_proba(features_df)[0]
                # Assuming binary classification, take probability of positive class
                probability = float(prediction[1] if len(prediction) > 1 else prediction[0])
            except Exception as e:
                print(f"Model prediction failed: {e}")
                # Fall back to baseline
                probability = self._baseline_prediction(features_df, trigger_type)
        else:
            # Use baseline prediction if no model loaded
            probability = self._baseline_prediction(features_df, trigger_type)
        
        # Calculate confidence intervals
        uncertainty = 0.15 if self.model is not None else 0.25  # Higher uncertainty for baseline
        confidence_lower, confidence_upper = self.calculate_confidence_intervals(probability, uncertainty)
        
        return ForecastCreate(
            forecast_date=start_date,
            target_date=target_date,
            horizon_months=horizon_months,
            trigger_type=trigger_type,
            probability=probability,
            confidence_lower=confidence_lower,
            confidence_upper=confidence_upper,
            model_version=self.model_version
        )
    
    def _baseline_prediction(self, features_df: pd.DataFrame, trigger_type: str) -> float:
        """
        Baseline prediction using simple heuristics
        
        Args:
            features_df: Feature DataFrame
            trigger_type: Type of trigger
            
        Returns:
            Probability estimate (0-1)
        """
        features = features_df.iloc[0]
        
        if trigger_type == "drought":
            # Low rainfall and high temperature indicate drought risk
            rainfall_score = 1.0 - min(1.0, features['avg_rainfall_30d'] / 100.0)
            temp_score = min(1.0, max(0.0, (features['avg_temp_30d'] - 25) / 10.0))
            ndvi_score = 1.0 - min(1.0, max(0.0, features['avg_ndvi_30d']))
            probability = (rainfall_score * 0.5 + temp_score * 0.3 + ndvi_score * 0.2)
            
        elif trigger_type == "flood":
            # High rainfall indicates flood risk
            rainfall_score = min(1.0, features['total_rainfall_30d'] / 300.0)
            probability = rainfall_score * 0.7 + 0.1  # Base 10% risk
            
        elif trigger_type == "crop_failure":
            # Combination of factors
            rainfall_score = abs(features['avg_rainfall_30d'] - 50) / 50.0  # Deviation from optimal
            ndvi_score = 1.0 - min(1.0, max(0.0, features['avg_ndvi_30d']))
            probability = (rainfall_score * 0.5 + ndvi_score * 0.5)
        else:
            probability = 0.2  # Default baseline
        
        return min(1.0, max(0.0, probability))


def generate_forecasts(
    db: Session,
    start_date: Optional[date] = None,
    horizons: List[int] = [3, 4, 5, 6]
) -> List[ForecastResponse]:
    """
    Generate forecasts for all trigger types and horizons
    
    Args:
        db: Database session
        start_date: Starting date (defaults to today)
        horizons: List of forecast horizons in months
        
    Returns:
        List of generated forecasts
    """
    if start_date is None:
        start_date = date.today()
    
    generator = ForecastGenerator()
    generator.load_model()
    
    trigger_types = ["drought", "flood", "crop_failure"]
    forecasts = []
    
    for trigger_type in trigger_types:
        for horizon in horizons:
            forecast_data = generator.generate_forecast(db, start_date, horizon, trigger_type)
            
            if forecast_data:
                # Check if forecast already exists
                existing = db.query(Forecast).filter(
                    and_(
                        Forecast.forecast_date == forecast_data.forecast_date,
                        Forecast.target_date == forecast_data.target_date,
                        Forecast.trigger_type == forecast_data.trigger_type
                    )
                ).first()
                
                if existing:
                    # Update existing forecast
                    for key, value in forecast_data.model_dump().items():
                        setattr(existing, key, value)
                    db.commit()
                    db.refresh(existing)
                    forecasts.append(ForecastResponse.model_validate(existing))
                else:
                    # Create new forecast
                    forecast = Forecast(**forecast_data.model_dump())
                    db.add(forecast)
                    db.commit()
                    db.refresh(forecast)
                    forecasts.append(ForecastResponse.model_validate(forecast))
    
    return forecasts


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
    end_date: Optional[date] = None
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
        
    Returns:
        List of matching forecasts
    """
    query = db.query(Forecast)
    
    if trigger_type:
        query = query.filter(Forecast.trigger_type == trigger_type)
    
    if min_probability is not None:
        query = query.filter(Forecast.probability >= min_probability)
    
    if horizon_months is not None:
        query = query.filter(Forecast.horizon_months == horizon_months)
    
    if start_date:
        query = query.filter(Forecast.target_date >= start_date)
    
    if end_date:
        query = query.filter(Forecast.target_date <= end_date)
    
    forecasts = query.order_by(desc(Forecast.target_date)).all()
    
    return [ForecastResponse.model_validate(f) for f in forecasts]



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
