"""
Historical Backtesting for Phase-Based Coverage Model (Daily Data)
==================================================================

Purpose: Validate Phase-Based Model (Moderate) using 10 years of daily NASA POWER data.
Compares:
1. Simple Seasonal Model (Total Rainfall < 400mm)
2. Phase-Based Model (Dynamic Start + 4 Phases + Dual-Index Triggers)

Data Source: outputs/raw/daily_climate_data_2015_2025.csv
Date: January 23, 2026
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.app.services.phase_based_coverage import PhaseBasedCoverageService
from backend.app.config.rice_growth_phases import PAYOUT_RATES

class HistoricalBacktester:
    """Backtest phase-based model against daily historical data"""
    
    def __init__(self, data_path: str):
        self.phase_service = PhaseBasedCoverageService()
        self.data_path = data_path
        
    def load_data(self) -> pd.DataFrame:
        """Load and prepare daily climate data"""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
            
        df = pd.read_csv(self.data_path)
        
        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Ensure required columns exist
        required = ['date', 'location', 'rainfall_mm', 'soil_moisture_index']
        if not all(col in df.columns for col in required):
            raise ValueError(f"Missing columns. Found: {df.columns}")
            
        # Map soil_moisture_index to soil_moisture (consistent naming)
        df['soil_moisture'] = df['soil_moisture_index']
        
        print(f"Loaded {len(df)} daily records")
        print(f"Locations: {df['location'].unique()}")
        print(f"Years: {df['year'].min()} - {df['year'].max()}")
        return df

    def get_season_data(self, df: pd.DataFrame, location: str, year: int) -> pd.DataFrame:
        """Get data for the growing season (March - August)"""
        # We need March for dynamic start monitoring
        # Season is ~145 days, so ending around July/August depending on start
        start_date = datetime(year, 3, 1)
        end_date = datetime(year, 8, 31)
        
        mask = (
            (df['location'] == location) & 
            (df['date'] >= start_date) & 
            (df['date'] <= end_date)
        )
        return df[mask].copy().sort_values('date')

    def calculate_simple_payout(self, season_df: pd.DataFrame) -> float:
        """
        Simple Model: Payout if total seasonal rainfall < 400mm
        (Fixed season: March 15 - August 7 approx)
        """
        if season_df.empty:
            return 0.0
            
        # Hardcoded season for simple model comparison (March 15 start)
        start_date = season_df['date'].min().replace(day=15)
        end_date = start_date + timedelta(days=145)
        
        mask = (season_df['date'] >= start_date) & (season_df['date'] < end_date)
        season_total = season_df.loc[mask, 'rainfall_mm'].sum()
        
        if season_total < 400:
            return PAYOUT_RATES['drought']
        return 0.0

    def run_backtest(self):
        """Execute backtest for all years and locations"""
        df = self.load_data()
        locations = df['location'].unique()
        years = sorted(df['year'].unique())
        
        results = []
        
        print("\nStarting Simulation...")
        print("=" * 80)
        print(f"{'Location':<15} {'Year':<6} {'Start':<12} {'Simple':<8} {'Phase':<8} {'Diff':<8} {'Events'}")
        print("-" * 80)
        
        for location in locations:
            for year in years:
                # 1. Get Season Data
                season_df = self.get_season_data(df, location, year)
                if season_df.empty:
                    continue
                
                # 2. Simple Model Result
                simple_payout = self.calculate_simple_payout(season_df)
                
                # 3. Phase-Based Model Result
                # 3a. Calculate Dynamic Start
                start_date, triggered, reason = self.phase_service.calculate_dynamic_start(
                    location, year, season_df[['date', 'rainfall_mm']]
                )
                
                # 3b. Calculate Payouts
                phase_result = self.phase_service.calculate_phase_payouts(
                    location=location,
                    coverage_start=start_date,
                    rainfall_data=season_df[['date', 'rainfall_mm']],
                    soil_moisture_data=season_df[['date', 'soil_moisture']],
                    sum_insured=90
                )
                
                moderate_payout = phase_result['total_payout']
                
                # 4. Record Result
                diff = moderate_payout - simple_payout
                triggers = phase_result['triggered_phases']
                
                results.append({
                    'location': location,
                    'year': year,
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'simple_payout': simple_payout,
                    'moderate_payout': moderate_payout,
                    'difference': diff,
                    'triggers': ", ".join(triggers) if triggers else "None",
                    'simple_triggered': simple_payout > 0,
                    'moderate_triggered': moderate_payout > 0
                })
                
                print(f"{location:<15} {year:<6} {start_date.strftime('%b %d'):<12} "
                      f"${simple_payout:<7.0f} ${moderate_payout:<7.2f} ${diff:<7.2f} "
                      f"{len(triggers)} phases")

        return pd.DataFrame(results)

    def save_results(self, results_df: pd.DataFrame):
        """Save results and summary stats"""
        output_dir = 'outputs/evaluation'
        os.makedirs(output_dir, exist_ok=True)
        
        # Save CSV
        csv_path = os.path.join(output_dir, 'phase_based_backtest_results_daily.csv')
        results_df.to_csv(csv_path, index=False)
        
        # Calculate Stats
        total_years = len(results_df)
        simple_hits = results_df['simple_triggered'].sum()
        mod_hits = results_df['moderate_triggered'].sum()
        
        summary = {
            'scenarios': total_years,
            'simple_model': {
                'payout_freq': float(simple_hits / total_years),
                'total_payout': float(results_df['simple_payout'].sum())
            },
            'moderate_model': {
                'payout_freq': float(mod_hits / total_years),
                'total_payout': float(results_df['moderate_payout'].sum())
            },
            'improvement': {
                'basis_risk_reduction': "Higher frequency implies detecting localized stress (reduced false negatives)" if mod_hits > simple_hits else "Lower frequency implies filtering false alarms",
                'net_difference': float(results_df['difference'].sum())
            }
        }
        
        import json
        json_path = os.path.join(output_dir, 'phase_based_backtest_summary_daily.json')
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=2)
            
        print("\n" + "=" * 80)
        print(f"Analysis Complete")
        print(f"Total Scenarios: {total_years}")
        print(f"Simple Model Frequency: {summary['simple_model']['payout_freq']:.1%}")
        print(f"Phase Model Frequency:  {summary['moderate_model']['payout_freq']:.1%}")
        print(f"Results saved to: {csv_path}")

if __name__ == "__main__":
    backtester = HistoricalBacktester('outputs/raw/daily_climate_data_2015_2025.csv')
    try:
        results = backtester.run_backtest()
        backtester.save_results(results)
    except Exception as e:
        print(f"\nCRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
