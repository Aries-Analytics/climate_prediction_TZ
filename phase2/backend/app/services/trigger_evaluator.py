from datetime import date
from typing import Optional, Dict, Any, List
from app.config.rice_thresholds import (
    KILOMBERO_WET_SEASON, 
    KILOMBERO_DRY_SEASON, 
    RAINFALL_THRESHOLDS,
    get_kilombero_stage
)

class TriggerEvaluator:
    """
    Evaluates climate forecasts against calibrated insurance thresholds
    to generate actionable alerts.
    """
    
    @staticmethod
    def determine_stage(target_date: date, season: str = 'wet_season') -> str:
        """
        Determine the phenology stage based on target date and season.
        """
        season_type = 'dry' if season == 'dry_season' else 'wet'
        return get_kilombero_stage(target_date, season_type)

    @staticmethod
    def evaluate_rainfall_trigger(
        forecast_rainfall: float,
        target_date: date,
        season: str = 'wet_season'
    ) -> Optional[Dict[str, Any]]:
        """
        Check if forecasted rainfall breaches any critical thresholds for the current stage.
        
        Returns:
            Dict representing TriggerAlert data if breach occurs, else None.
        """
        stage = TriggerEvaluator.determine_stage(target_date, season)
        
        if stage == 'off_season' or stage not in RAINFALL_THRESHOLDS:
            return None
            
        thresholds = RAINFALL_THRESHOLDS[stage]
        min_threshold = thresholds.get('min', 0)
        max_threshold = thresholds.get('excessive', 9999)
        optimal = thresholds.get('optimal', 100)
        
        # 1. Check for Deficit (Drought Risk)
        if forecast_rainfall < min_threshold:
            deficit_amount = min_threshold - forecast_rainfall
            severity = 'critical' if forecast_rainfall < (min_threshold * 0.7) else 'warning'
            
            return {
                'alert_type': 'rainfall_deficit',
                'severity': severity,
                'phenology_stage': stage,
                'threshold_value': min_threshold,
                'forecast_value': forecast_rainfall,
                'deviation': -deficit_amount,
                'recommended_action': TriggerEvaluator._get_action('deficit', severity, stage),
                'urgency_days': 7 if severity == 'critical' else 14
            }
            
        # 2. Check for Excess (Flood Risk / Crop Damage)
        elif forecast_rainfall > max_threshold:
            excess_amount = forecast_rainfall - max_threshold
            severity = 'critical' if forecast_rainfall > (max_threshold * 1.5) else 'warning'
            
            return {
                'alert_type': 'excessive_rainfall',
                'severity': severity,
                'phenology_stage': stage,
                'threshold_value': max_threshold,
                'forecast_value': forecast_rainfall,
                'deviation': excess_amount,
                'recommended_action': TriggerEvaluator._get_action('excess', severity, stage),
                'urgency_days': 3 if severity == 'critical' else 7
            }
            
        return None

    @staticmethod
    def _get_action(risk_type: str, severity: str, stage: str) -> str:
        """Generate specific actionable recommendation."""
        if risk_type == 'deficit':
            if stage == 'germination':
                return "Delay planting or irrigate immediately if already planted." if severity == 'critical' else "Monitor soil moisture closely."
            elif stage == 'flowering':
                return "CRITICAL: Arrange emergency irrigation to save yield." if severity == 'critical' else "Conserve water; yield reduction likely."
            else:
                return "Consider supplemental irrigation."
                
        elif risk_type == 'excess':
            if stage == 'harvesting':
                return "RUSH HARVEST: Rain will damage grain quality."
            else:
                return "Ensure field drainage channels are clear."
        
        return "Monitor specific field conditions."
