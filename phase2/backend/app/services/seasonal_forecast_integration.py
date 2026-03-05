"""
Seasonal Forecast Service with Phase-Based Coverage Integration
Bridges automated forecasting with parametric insurance triggers

Version: 1.0
Date: January 23, 2026
"""

from datetime import datetime, timedelta, date, timezone
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from app.services.phase_based_coverage import PhaseBasedCoverageService
from app.config.rice_growth_phases import RICE_GROWTH_PHASES, PAYOUT_RATES
from app.models.forecast import Forecast
from app.models.location import Location


class SeasonalForecastService:
    """
    Generates seasonal forecasts for rice growing season (Mar-Jun)
    Integrates phase-based coverage for insurance trigger predictions
    """
    
    def __init__(self):
        self.phase_service = PhaseBasedCoverageService()
        self.season_months = [3, 4, 5, 6]  # Mar-Jun
        
    def generate_seasonal_forecast(
        self,
        db: Session,
        location: str,
        year: int,
        monthly_forecasts: List[Dict]
    ) -> Dict:
        """
        Generate seasonal forecast from monthly predictions
        
        Args:
            db: Database session
            location: Location name
            year: Forecast year
            monthly_forecasts: List of monthly forecast dicts with rainfall_mm predictions
            
        Returns:
            Seasonal forecast dict with trigger probabilities and phase breakdown
        """
        # Aggregate monthly forecasts to seasonal
        seasonal_total_mm = sum(f['rainfall_mm'] for f in monthly_forecasts if f['month'] in self.season_months)
        
        # Calculate phase-based triggers (PRODUCTION MODEL)
        # Note: Simple model kept only in docs for validation purposes
        coverage_start = datetime(year, 3, 1)
        
        # Create rainfall projection dataframe
        rainfall_projection = self._create_rainfall_projection(
            monthly_forecasts,
            coverage_start
        )
        
        # Get phase-based prediction
        try:
            phase_result = self.phase_service.calculate_phase_payouts(
                location=location,
                coverage_start=coverage_start,
                rainfall_data=rainfall_projection,
                soil_moisture_data=None,  # Future enhancement
                sum_insured=90
            )
            
            moderate_payout = phase_result['total_payout']
            phases_detail = phase_result['phases']
            
        except Exception as e:
            # Fallback to simple if phase calculation fails
            moderate_payout = 0.0  # Safe default: no payout when phase calc fails
            phases_detail = {'error': str(e)}
        
        # Calculate trigger probabilities (simplified - based on uncertainty)
        drought_prob = self._calculate_trigger_probability(seasonal_total_mm, 400, uncertainty=50)
        flood_prob = self._calculate_flood_probability(monthly_forecasts)
        
        return {
            'location': location,
            'forecast_year': year,
            'season': 'Mar-Jun',
            'forecast_date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            
            # Seasonal totals
            'predicted_seasonal_mm': round(seasonal_total_mm, 1),
            
            'drought_probability': drought_prob,
            'flood_probability': flood_prob,
            'expected_payout_per_farmer': round(moderate_payout * drought_prob, 2),
            'risk_level': self._assess_risk_level(drought_prob, flood_prob),
            'phase_breakdown': phases_detail,
            'confidence': 'MEDIUM'  # Based on forecast uncertainty
        }
    
    def _create_rainfall_projection(
        self,
        monthly_forecasts: List[Dict],
        coverage_start: datetime
    ) -> pd.DataFrame:
        """
        Convert monthly forecasts to daily rainfall projection for phase service
        Distributes monthly total evenly across days (simplified)
        """
        projections = []
        current_date = coverage_start
        
        for forecast in monthly_forecasts:
            if forecast['month'] not in self.season_months:
                continue
            
            # Get days in month
            if forecast['month'] == 2:
                days_in_month = 28
            elif forecast['month'] in [4, 6, 9, 11]:
                days_in_month = 30
            else:
                days_in_month = 31
            
            # Distribute monthly rainfall across days (simplified uniform distribution)
            daily_mm = forecast['rainfall_mm'] / days_in_month
            
            for day in range(days_in_month):
                projections.append({
                    'date': current_date + timedelta(days=day),
                    'rainfall_mm': daily_mm
                })
            
            current_date = current_date + timedelta(days=days_in_month)
        
        return pd.DataFrame(projections)
    
    def _calculate_trigger_probability(
        self,
        predicted_value: float,
        threshold: float,
        uncertainty: float = 50
    ) -> float:
        """
        Calculate probability of trigger based on prediction and uncertainty
        Uses normal distribution assumption
        """
        if predicted_value < threshold:
            # Below threshold - higher probability of trigger
            z_score = (threshold - predicted_value) / uncertainty
            prob = 0.5 + 0.5 * min(z_score, 1.0)
        else:
            # Above threshold - lower probability
            z_score = (predicted_value - threshold) / uncertainty
            prob = 0.5 - 0.5 * min(z_score, 1.0)
        
        return max(0.0, min(1.0, prob))
    
    def _calculate_flood_probability(self, monthly_forecasts: List[Dict]) -> float:
        """Estimate flood probability from monthly forecasts"""
        # Simplified: If any month has very high rainfall
        max_monthly = max(f['rainfall_mm'] for f in monthly_forecasts if f['month'] in self.season_months)
        
        if max_monthly > 250:  # Very high monthly total
            return 0.15
        elif max_monthly > 200:
            return 0.08
        else:
            return 0.03
    
    def _assess_risk_level(self, drought_prob: float, flood_prob: float) -> str:
        """Assess overall risk level for portfolio"""
        max_prob = max(drought_prob, flood_prob)
        
        if max_prob > 0.5:
            return 'HIGH'
        elif max_prob > 0.3:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def update_dashboard_data(
        self,
        db: Session,
        seasonal_forecast: Dict
    ) -> Dict:
        """
        Prepare data structure for risk management dashboard
        Includes both simple and phase-based model outputs
        """
        return {
            'seasonal_forecast': seasonal_forecast,
            
            # For dashboard display
            'dashboard_summary': {
                'location': seasonal_forecast['location'],
                'season': seasonal_forecast['season'],
                'predicted_rainfall': seasonal_forecast['predicted_seasonal_mm'],
                
                # Model comparison table
                'model_comparison': [
                    {
                        'model': 'Simple (Current)',
                        'method': '400mm threshold',
                        'payout': seasonal_forecast['simple_model']['payout'],
                        'triggered': seasonal_forecast['simple_model']['drought_triggered']
                    },
                    {
                        'model': 'Phase-Based (HewaSense)',
                        'method': '4-phase weighted',
                        'payout': seasonal_forecast['phase_based_model']['payout'],
                        'phases_triggered': seasonal_forecast['phase_based_model']['phases_triggered'],
                        'recommended': True
                    }
                ],
                
                # Risk metrics
                'drought_risk': f"{seasonal_forecast['trigger_probabilities']['drought']*100:.0f}%",
                'flood_risk': f"{seasonal_forecast['trigger_probabilities']['flood']*100:.0f}%",
                'risk_level': seasonal_forecast['risk_level'],
                'expected_payout_per_farmer': seasonal_forecast['expected_payout'],
                
                # Phase breakdown (for detail view)
                'phase_breakdown': seasonal_forecast['phase_based_model']['phases_detail']
            }
        }


# Integration function for automated pipeline
def generate_seasonal_forecast_from_pipeline(
    db: Session,
    location_id: int,
    year: int,
    monthly_forecast_ids: List[int]
) -> Dict:
    """
    Called by automated pipeline to generate seasonal forecast
    
    Args:
        db: Database session
        location_id: Location ID
        year: Forecast year
        monthly_forecast_ids: IDs of monthly forecasts to aggregate
        
    Returns:
        Seasonal forecast dict
    """
    service = SeasonalForecastService()
    
    # Fetch monthly forecasts from database
    monthly_forecasts = []
    for forecast_id in monthly_forecast_ids:
        forecast = db.query(Forecast).filter(Forecast.id == forecast_id).first()
        if forecast:
            monthly_forecasts.append({
                'month': forecast.forecast_month.month,
                'rainfall_mm': forecast.predicted_value,  # Adjust field name as needed
                'confidence': forecast.confidence
            })
    
    # Get location
    location = db.query(Location).filter(Location.id == location_id).first()
    location_name = location.name if location else f"Location_{location_id}"
    
    # Generate seasonal forecast
    seasonal_forecast = service.generate_seasonal_forecast(
        db, location_name, year, monthly_forecasts
    )
    
    # Prepare dashboard data
    dashboard_data = service.update_dashboard_data(db, seasonal_forecast)
    
    return dashboard_data


if __name__ == "__main__":
    # Test with sample data
    service = SeasonalForecastService()
    
    # Sample monthly forecasts
    sample_forecasts = [
        {'month': 3, 'rainfall_mm': 95},
        {'month': 4, 'rainfall_mm': 110},
        {'month': 5, 'rainfall_mm': 85},
        {'month': 6, 'rainfall_mm': 90}
    ]
    
    result = service.generate_seasonal_forecast(
        db=None,
        location='Morogoro',
        year=2026,
        monthly_forecasts=sample_forecasts
    )
    
    print("Seasonal Forecast Integration Test")
    print("=" * 60)
    print(f"Location: {result['location']}")
    print(f"Season: {result['season']}")
    print(f"Predicted Total: {result['predicted_seasonal_mm']}mm")
    print(f"\nSimple Model Payout: ${result['simple_model']['payout']}")
    print(f"Phase-Based Payout: ${result['phase_based_model']['payout']}")
    print(f"Difference: ${result['model_comparison']['payout_difference']}")
    print(f"\nDrought Probability: {result['trigger_probabilities']['drought']*100:.1f}%")
    print(f"Risk Level: {result['risk_level']}")
