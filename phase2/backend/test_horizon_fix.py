"""
Quick test to verify horizon-based probability adjustment works
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from datetime import date, timedelta
from app.core.database import SessionLocal
from app.services.forecast_service import ForecastGenerator
from app.models.climate_data import ClimateData
import pandas as pd

def test_horizon_adjustment():
    """Test that probabilities vary by horizon"""
    db = SessionLocal()
    
    try:
        # Create some dummy climate data for testing
        today = date.today()
        for i in range(90):
            test_date = today - timedelta(days=i)
            existing = db.query(ClimateData).filter(ClimateData.date == test_date).first()
            if not existing:
                climate_data = ClimateData(
                    date=test_date,
                    temperature_avg=28.0,
                    rainfall_mm=50.0,
                    ndvi=0.6,
                    enso_index=0.5,
                    iod_index=0.2
                )
                db.add(climate_data)
        db.commit()
        
        # Generate forecasts for different horizons
        generator = ForecastGenerator()
        
        print("\n" + "=" * 60)
        print("TESTING HORIZON-BASED PROBABILITY ADJUSTMENT")
        print("=" * 60)
        print("\nUsing identical climate conditions for all horizons...")
        print("Expected: Probabilities should DIFFER by horizon\n")
        
        for trigger_type in ["drought", "flood", "crop_failure"]:
            print(f"\n{trigger_type.upper()}:")
            print("-" * 40)
            
            probabilities = {}
            for horizon in [3, 4, 5, 6]:
                forecast = generator.generate_forecast(db, today, horizon, trigger_type)
                if forecast:
                    probabilities[horizon] = forecast.probability
                    print(f"  {horizon} months: {forecast.probability:.1%} "
                          f"(CI: [{forecast.confidence_lower:.1%}, {forecast.confidence_upper:.1%}])")
            
            # Check if probabilities are different
            unique_probs = len(set(probabilities.values()))
            if unique_probs == 1:
                print(f"  ❌ PROBLEM: All horizons have SAME probability!")
            else:
                print(f"  ✓ GOOD: {unique_probs} different probabilities across horizons")
        
        print("\n" + "=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)
        
    finally:
        db.close()

if __name__ == '__main__':
    test_horizon_adjustment()
