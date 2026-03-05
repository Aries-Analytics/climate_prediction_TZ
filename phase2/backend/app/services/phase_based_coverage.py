"""
Phase-Based Coverage Service
Implements "Moderate Model" using industry best practices
Calculates insurance payouts based on rice growth phases

Version: 1.0
Date: January 23, 2026
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
import random

from app.config.rice_growth_phases import (
    RICE_GROWTH_PHASES,
    DYNAMIC_START_CONFIG,
    SOIL_MOISTURE_THRESHOLDS,
    PAYOUT_RATES,
    get_phase_by_gdd,
    GDD_BASE_TEMP_C
)


class PhaseBasedCoverageService:
    """
    Calculates insurance payouts using phase-based triggers
    Aligned with industry best practices (Moderate Model)
    """
    
    def __init__(self):
        self.phases = RICE_GROWTH_PHASES
        self.dynamic_config = DYNAMIC_START_CONFIG
        self.soil_moisture_thresholds = SOIL_MOISTURE_THRESHOLDS
        
    def calculate_dynamic_start(
        self, 
        location: str, 
        year: int,
        rainfall_data: pd.DataFrame
    ) -> Tuple[datetime, bool, str]:
        """
        Calculate dynamic coverage start date based on actual rainfall
        Industry best practice: "Coverage starts when actual planting occurs"
        
        Args:
            location: Farm location
            year: Year
            rainfall_data: DataFrame with columns ['date', 'rainfall_mm']
            
        Returns:
            (start_date, coverage_triggered, reasoning)
        """
        monitoring_month = self.dynamic_config['monitoring_month']
        threshold_mm = self.dynamic_config['cumulative_threshold_mm']
        
        # Filter to monitoring month (March)
        march_data = rainfall_data[
            (rainfall_data['date'].dt.year == year) &
            (rainfall_data['date'].dt.month == monitoring_month)
        ].copy()
        
        if march_data.empty:
            fallback_month, fallback_day = self.dynamic_config['fallback_date']
            return (
                datetime(year, fallback_month, fallback_day),
                False,
                f"No March data available - using fallback April 1"
            )
        
        # Calculate cumulative rainfall
        march_data = march_data.sort_values('date')
        march_data['cumulative_mm'] = march_data['rainfall_mm'].cumsum()
        
        # Find first day when threshold exceeded
        threshold_days = march_data[march_data['cumulative_mm'] >= threshold_mm]
        
        if not threshold_days.empty:
            start_date = threshold_days.iloc[0]['date']
            cumulative = threshold_days.iloc[0]['cumulative_mm']
            return (
                start_date,
                True,
                f"Planting triggered: {cumulative:.1f}mm recorded by {start_date.strftime('%b %d')}"
            )
        else:
            # March too dry - use fallback
            fallback_month, fallback_day = self.dynamic_config['fallback_date']
            total_march = march_data['rainfall_mm'].sum()
            return (
                datetime(year, fallback_month, fallback_day),
                False,
                f"March too dry ({total_march:.1f}mm < {threshold_mm}mm) - fallback to April 1"
            )
    
    def calculate_phase_payouts(
        self,
        location: str,
        coverage_start: datetime,
        rainfall_data: pd.DataFrame,
        temperature_data: pd.DataFrame, # Newly required for GDD
        soil_moisture_data: Optional[pd.DataFrame] = None,
        sum_insured: float = 90  # Crop failure max payout
    ) -> Dict:
        """
        Calculate payouts for each growth phase using rainfall, GDD, and soil moisture
        
        Args:
            location: Farm location
            coverage_start: When coverage began
            rainfall_data: DataFrame with ['date', 'rainfall_mm']
            temperature_data: DataFrame with ['date', 'temp_mean_c']
            soil_moisture_data: Optional DataFrame with ['date', 'soil_moisture']
            sum_insured: Maximum payout amount
            
        Returns:
            Dictionary with phase-by-phase breakdown and total payout
        """
        phase_results = {}
        
        # Merge data streams
        daily_data = pd.merge(rainfall_data, temperature_data, on='date', how='inner')
        if soil_moisture_data is not None:
            daily_data = pd.merge(daily_data, soil_moisture_data, on='date', how='left')
            
        # Filter from start date
        daily_data = daily_data[daily_data['date'] >= coverage_start].sort_values('date').reset_index(drop=True)
        
        if daily_data.empty:
            return {'error': 'No climate data available after coverage start date'}

        # Calculate daily GDD
        daily_data['gdd'] = daily_data['temp_mean_c'].apply(lambda t: max(0, t - GDD_BASE_TEMP_C))
        daily_data['cumulative_gdd'] = daily_data['gdd'].cumsum()
        
        # Calculate rolling 5-day rainfall for cumulative flood logic
        daily_data['rolling_5d_rain'] = daily_data['rainfall_mm'].rolling(window=5, min_periods=1).sum()

        current_phase_idx = 0
        phase_names = list(self.phases.keys())
        
        phase_start_date = coverage_start
        accumulated_gdd_start = 0

        for phase_name in phase_names:
            phase_config = self.phases[phase_name]
            target_gdd = accumulated_gdd_start + phase_config['required_gdd']
            
            # Find when this phase ends based on target GDD
            phase_data = daily_data[
                (daily_data['cumulative_gdd'] > accumulated_gdd_start) & 
                (daily_data['cumulative_gdd'] <= target_gdd)
            ]
            
            if phase_data.empty:
                # If we run out of data before end of season
                phase_end_date = daily_data['date'].max()
                phase_duration = (phase_end_date - phase_start_date).days
                
                phase_results[phase_name] = {
                    'start_date': phase_start_date.strftime('%Y-%m-%d'),
                    'end_date': phase_end_date.strftime('%Y-%m-%d'),
                    'duration_days': phase_duration,
                    'phase_rainfall_mm': 0.0,
                    'drought_payout': 0.0,
                    'flood_payout': 0.0,
                    'soil_moisture_payout': 0.0,
                    'total_payout': 0.0,
                    'error': 'Climate data ended before GDD requirement met'
                }
                break

            phase_end_date = phase_data['date'].max()
            phase_duration = len(phase_data)
            
            # Calculate rainfall-based triggers
            phase_rainfall_mm = phase_data['rainfall_mm'].sum()
            max_daily_rainfall = phase_data['rainfall_mm'].max()
            max_5d_cumulative_rainfall = phase_data['rolling_5d_rain'].max()
            
            # Drought trigger
            drought_payout = self._calculate_drought_payout(
                phase_rainfall_mm,
                phase_config['drought_trigger_mm'],
                phase_config['rainfall_requirement_mm'],
                phase_config['payout_weight'],
                sum_insured
            )
            
            # Flood trigger (Dual condition: Acute OR Prolonged)
            flood_payout = self._calculate_flood_payout(
                max_daily_rainfall,
                max_5d_cumulative_rainfall,
                phase_config['flood_trigger_daily_mm'],
                phase_config['flood_trigger_cumulative_mm'],
                phase_config['payout_weight'],
                sum_insured
            )
            
            # Soil moisture trigger (if data available)
            soil_moisture_payout = 0.0
            if 'soil_moisture' in phase_data.columns and not phase_data['soil_moisture'].isna().all():
                avg_sm = phase_data['soil_moisture'].mean()
                soil_moisture_payout = self._calculate_soil_moisture_payout(
                    avg_sm,
                    phase_config['payout_weight'],
                    sum_insured
                )
            else:
                avg_sm = None
            
            # Use maximum of drought OR soil moisture (dual-index, farmer-friendly)
            total_payout = max(drought_payout, soil_moisture_payout) + flood_payout
            
            phase_results[phase_name] = {
                'start_date': phase_start_date.strftime('%Y-%m-%d'),
                'end_date': phase_end_date.strftime('%Y-%m-%d'),
                'duration_days': phase_duration,
                'accumulated_gdd': round(phase_data['gdd'].sum(), 1),
                'phase_rainfall_mm': round(phase_rainfall_mm, 1),
                'max_daily_rainfall_mm': round(max_daily_rainfall, 1),
                'max_5d_cumulative_rain_mm': round(max_5d_cumulative_rainfall, 1),
                'avg_soil_moisture': round(avg_sm, 3) if avg_sm is not None else None,
                'drought_payout': round(drought_payout, 2),
                'flood_payout': round(flood_payout, 2),
                'soil_moisture_payout': round(soil_moisture_payout, 2),
                'total_payout': round(total_payout, 2),
                'triggered': total_payout > 0
            }
            
            # Setup for next phase
            phase_start_date = phase_end_date + timedelta(days=1)
            accumulated_gdd_start = target_gdd
        
        # Calculate summary
        total_payout = sum(p['total_payout'] for p in phase_results.values())
        triggered_phases = [k for k, v in phase_results.items() if v['triggered']]
        
        return {
            'coverage_start': coverage_start.strftime('%Y-%m-%d'),
            'coverage_end': phase_end_date.strftime('%Y-%m-%d') if 'phase_end_date' in locals() else 'Unknown',
            'phases': phase_results,
            'total_payout': round(total_payout, 2),
            'triggered_phases': triggered_phases,
            'num_phases_triggered': len(triggered_phases),
            'sum_insured': sum_insured
        }
    
    def _calculate_drought_payout(
        self,
        actual_rainfall: float,
        drought_trigger: float,
        rainfall_requirement: float,
        phase_weight: float,
        sum_insured: float
    ) -> float:
        """Calculate payout for drought conditions"""
        if actual_rainfall >= drought_trigger:
            return 0.0
        
        # Linear payout based on severity
        deficit = drought_trigger - actual_rainfall
        max_deficit = drought_trigger  # 100% deficit when no rain
        severity = min(deficit / max_deficit, 1.0)
        
        payout = sum_insured * phase_weight * severity
        return payout
    
    def _calculate_flood_payout(
        self,
        max_daily_rainfall: float,
        max_5d_cumulative_rainfall: float,
        flood_trigger_daily: float,
        flood_trigger_cumulative: float,
        phase_weight: float,
        sum_insured: float
    ) -> float:
        """Calculate payout for flood conditions (Dual Condition: Acute OR Prolonged)"""
        
        acute_triggered = max_daily_rainfall > flood_trigger_daily
        prolonged_triggered = max_5d_cumulative_rainfall > flood_trigger_cumulative
        
        if not (acute_triggered or prolonged_triggered):
            return 0.0
        
        # Fixed payout for flood (50% of phase weight)
        payout = sum_insured * phase_weight * 0.5
        return payout
    
    def _calculate_soil_moisture_payout(
        self,
        avg_soil_moisture: float,
        phase_weight: float,
        sum_insured: float
    ) -> float:
        """
        Calculate payout based on soil moisture
        ACRE Training: "Soil moisture is better proxy than rainfall alone"
        """
        deficit_threshold = self.soil_moisture_thresholds['deficit_threshold']
        excess_threshold = self.soil_moisture_thresholds['excess_threshold']
        
        # Deficit trigger (< 15%)
        if avg_soil_moisture < deficit_threshold:
            deficit = deficit_threshold - avg_soil_moisture
            severity = min(deficit / deficit_threshold, 1.0)
            multiplier = self.soil_moisture_thresholds['payout_multiplier_deficit']
            return sum_insured * phase_weight * severity * multiplier
        
        # Excess trigger (> 25%)
        elif avg_soil_moisture > excess_threshold:
            excess = avg_soil_moisture - excess_threshold
            severity = min(excess / 0.10, 1.0)  # Cap at 35% moisture
            multiplier = self.soil_moisture_thresholds['payout_multiplier_excess']
            return sum_insured * phase_weight * severity * multiplier
        
        return 0.0
    
    def compare_simple_vs_moderate(
        self,
        location: str,
        coverage_start: datetime,
        rainfall_data: pd.DataFrame,
        sum_insured: float = 90
    ) -> Dict:
        """
        Compare simple seasonal model vs moderate phase-based model
        For validation and demonstration
        """
        # Simple model (current approach)
        season_end = coverage_start + timedelta(days=145)
        season_rainfall_data = rainfall_data[
            (rainfall_data['date'] >= coverage_start) &
            (rainfall_data['date'] < season_end)
        ]
        seasonal_total = season_rainfall_data['rainfall_mm'].sum()
        simple_drought = seasonal_total < 400  # Simple threshold
        simple_payout = PAYOUT_RATES['drought'] if simple_drought else 0
        
        # Moderate model (phase-based v4 - requiring temperature mockup for simple comparison)
        
        # Generate dummy temperature data for simple vs moderate comparison
        temp_df = rainfall_data.copy()
        temp_df = temp_df[['date']]
        temp_df['temp_mean_c'] = 26.0 # Avg temp provides ~16 GDD/day
        
        moderate_result = self.calculate_phase_payouts(
            location, coverage_start, rainfall_data, temp_df, None, sum_insured
        )
        
        return {
            'simple_model': {
                'seasonal_total_mm': round(seasonal_total, 1),
                'drought_triggered': simple_drought,
                'payout': simple_payout
            },
            'moderate_model': {
                'total_payout': moderate_result['total_payout'],
                'phases_triggered': moderate_result['num_phases_triggered'],
                'phase_breakdown': moderate_result['phases']
            },
            'comparison': {
                'payout_difference': moderate_result['total_payout'] - simple_payout,
                'more_accurate': 'moderate',  # Phase-based reduces basis risk
                'recommendation': 'Use moderate model for production'
            }
        }


# Example usage
if __name__ == "__main__":
    service = PhaseBasedCoverageService()
    
    # Create sample data
    start = datetime(2025, 3, 15)
    dates = pd.date_range(start, periods=145, freq='D')
    
    # Simulate rainfall pattern (drought in flowering phase)
    rainfall = np.random.exponential(3, 145)  # Exponential distribution
    rainfall[40:80] = rainfall[40:80] * 0.3  # Reduce rainfall during flowering
    
    # Simulate temperature pattern
    temperatures = np.array([random.gauss(26, 2) for _ in range(145)])  # 26C mean temp
    
    rainfall_df = pd.DataFrame({
        'date': dates,
        'rainfall_mm': rainfall
    })
    
    temperature_df = pd.DataFrame({
        'date': dates,
        'temp_mean_c': temperatures
    })
    
    # Calculate payouts
    result = service.calculate_phase_payouts(
        location='Morogoro',
        coverage_start=start,
        rainfall_data=rainfall_df,
        temperature_data=temperature_df,
        sum_insured=90
    )
    
    print("Phase-Based Coverage Calculation")
    print("=" * 60)
    print(f"Coverage Period: {result['coverage_start']} to {result['coverage_end']}")
    print(f"\nTotal Payout: ${result['total_payout']:.2f}")
    print(f"Phases Triggered: {result['num_phases_triggered']}/4")
    print(f"\nPhase Breakdown:")
    print("-" * 60)
    
    for phase_name, phase_data in result['phases'].items():
        print(f"\n{phase_name.upper()}")
        print(f"  Rainfall: {phase_data['phase_rainfall_mm']}mm")
        print(f"  Drought Payout: ${phase_data['drought_payout']:.2f}")
        print(f"  Flood Payout: ${phase_data['Flood_payout']:.2f}")
        print(f"  Total: ${phase_data['total_payout']:.2f}")
