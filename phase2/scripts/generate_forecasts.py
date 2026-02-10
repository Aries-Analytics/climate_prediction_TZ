#!/usr/bin/env python3
"""
Generate forecasts for Early Warning Dashboard

This script generates forecasts using the forecast service and populates
recommendations for high-risk predictions.

Usage (from container):
  docker exec climate_backend_dev python -c "from scripts.generate_forecasts import main; main()"
  
Or manually from backend directory:
  cd backend && python -c "import sys; sys.path.insert(0, '..'); from scripts.generate_forecasts import main; main()"
"""

import sys
import os

# Ensure we're in the backend directory for imports
# Ensure we're in the backend directory for imports
# In Docker, root IS the backend. Locally, it might be in 'backend/' subdir.
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

# If 'backend' subdirectory exists (local dev), add it too
backend_dir = os.path.join(root_dir, 'backend')
if os.path.exists(backend_dir):
    sys.path.insert(0, backend_dir)

from datetime import date
from sqlalchemy import func
from app.core.database import SessionLocal
from app.services.forecast_service import generate_forecasts_all_locations, generate_all_recommendations
from app.models.climate_data import ClimateData
from app.models.climate_forecast import ClimateForecast
from app.models.forecast import Forecast
from app.models.trigger_alert import TriggerAlert

def main():
    """Generate forecasts and recommendations"""
    print("=" * 60)
    print("GENERATING FORECASTS FOR ALL 6 LOCATIONS")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # OPTION A: Use latest available climate data date as forecast base
        # This handles data latency where some sources may not have current month data
        print("\nDetermining forecast base date...")
        latest_climate_date = db.query(func.max(ClimateData.date)).scalar()
        
        if latest_climate_date is None:
            print("ERROR: No climate data found in database!")
            print("Run: python scripts/load_dashboard_data.py --clear")
            return
        
        today = date.today()
        data_age_days = (today - latest_climate_date).days
        
        print(f"   Today: {today}")
        print(f"   Latest climate data: {latest_climate_date}")
        print(f"   Data age: {data_age_days} days")
        
        if data_age_days > 90:
            print(f"   WARNING: Climate data is {data_age_days} days old!")
            print(f"   Consider updating data sources.")
        
        # Use latest available data as forecast base (industry best practice)
        forecast_base_date = latest_climate_date
        print(f"\n   Using forecast base date: {forecast_base_date}")
        print(f"   (Industry standard: use latest complete validated data)\n")
        
        # Cleanup existing forecasts for this base date
        forecast_date = forecast_base_date
        print(f"Cleaning up existing forecasts for {forecast_date}...")
        try:
             # Delete related alerts first (foreign key constraint)
            db.query(TriggerAlert).filter(TriggerAlert.date_generated == forecast_date).delete()
            
            # Delete dependent climate forecasts 
            db.query(ClimateForecast).filter(ClimateForecast.forecast_date == forecast_date).delete()
            
            # Delete main forecasts
            db.query(Forecast).filter(Forecast.forecast_date == forecast_date).delete()
            
            db.commit()
            print("   Cleanup complete.")
        except Exception as e:
            db.rollback()
            print(f"   Cleanup failed (might be empty): {e}")

        # Generate forecasts for all locations with 3-6 month horizons
        print("\nGenerating forecasts for all locations...")
        print(f"   Forecast base date: {forecast_base_date}")
        print(f"   Horizons: 3, 4, 5, 6 months")
        print(f"   Target dates: {forecast_base_date.replace(month=forecast_base_date.month+3 if forecast_base_date.month<=9 else forecast_base_date.month-9)} to {forecast_base_date.replace(month=forecast_base_date.month+6 if forecast_base_date.month<=6 else forecast_base_date.month-6)}" if forecast_base_date.month <= 6 else f"(varies by location)")
        print(f"   Trigger types: Drought, Flood, Crop Failure")
        print(f"   Generating for ALL locations in database...\n")
        
        forecasts = generate_forecasts_all_locations(
            db=db,
            start_date=forecast_base_date,  # Use latest available data, not today
            horizons=[3, 4, 5, 6]
        )
        
        print(f"\nGenerated {len(forecasts)} forecasts")
        
        # Show forecast summary
        for i, f in enumerate(forecasts, 1):
            print(f"   {i}. {f.trigger_type} ({f.horizon_months}mo): {f.probability:.1%} probability")
        
        # Generate recommendations for high-risk forecasts
        print(f"\nGenerating recommendations (threshold: >30% probability)...")
        recommendations = generate_all_recommendations(db, min_probability=0.3)
        
        print(f"Generated {len(recommendations)} recommendations")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. Priority: {rec.priority.upper()} - {rec.recommendation_text[:60]}...")
        
        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print(f"\nDatabase updated with:")
        print(f"   - {len(forecasts)} forecasts")
        print(f"   - {len(recommendations)} recommendations")
        print("\nNext steps:")
        print("   1. Refresh the Early Warning dashboard")
        print("   2. View forecasts at http://localhost:3000")
        print("   3. Check recommendations panel")
        
    except Exception as e:
        print(f"\nError generating forecasts: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
