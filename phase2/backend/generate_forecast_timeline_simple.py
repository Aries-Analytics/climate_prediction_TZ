"""
Generate forecasts for multiple dates to create a timeline.
Uses existing climate data in the database.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.services.forecast_service import generate_forecasts, generate_all_recommendations
from app.models.climate_data import ClimateData
from sqlalchemy import func
from datetime import timedelta

db = SessionLocal()

try:
    # Find the latest climate data date
    latest_climate_date = db.query(func.max(ClimateData.date)).scalar()
    
    if not latest_climate_date:
        print("❌ No climate data found in database")
        exit(1)
    
    print("=" * 70)
    print("FORECAST TIMELINE GENERATION")
    print("=" * 70)
    print(f"\nLatest climate data: {latest_climate_date}")
    print("\n📌 IMPORTANT: Forecasts ARE for future dates!")
    print("   - Forecast Date = When we make the forecast (needs climate data)")
    print("   - Target Date = Future date we're predicting (3-6 months ahead)")
    print(f"\n   Example: Forecast from {latest_climate_date} predicts")
    print(f"            {latest_climate_date + timedelta(days=90)} to {latest_climate_date + timedelta(days=180)}\n")
    
    # Generate forecasts for the past 8 weeks (every week) to create a timeline
    forecast_dates = []
    start_date = latest_climate_date - timedelta(weeks=8)
    
    for week in range(9):  # 0 to 8 weeks ago (9 data points)
        forecast_date = start_date + timedelta(weeks=week)
        if forecast_date <= latest_climate_date:
            forecast_dates.append(forecast_date)
    
    print(f"Generating forecasts for {len(forecast_dates)} dates...")
    print(f"Forecast dates: {forecast_dates[0]} to {forecast_dates[-1]}")
    
    target_start = forecast_dates[0] + timedelta(days=90)
    target_end = forecast_dates[-1] + timedelta(days=180)
    print(f"Will predict: {target_start} to {target_end}\n")
    
    # Generate forecasts
    horizons = [3, 4, 5, 6]
    all_forecasts = []
    
    for i, forecast_date in enumerate(forecast_dates, 1):
        target_start = forecast_date + timedelta(days=90)
        target_end = forecast_date + timedelta(days=180)
        print(f"[{i}/{len(forecast_dates)}] From {forecast_date} → predicting {target_start} to {target_end}")
        
        try:
            forecasts = generate_forecasts(db, forecast_date, horizons)
            print(f"         ✓ Generated {len(forecasts)} forecasts")
            all_forecasts.extend(forecasts)
        except Exception as e:
            print(f"         ✗ Error: {e}")
    
    print(f"\n{'=' * 70}")
    print(f"✅ COMPLETE: Generated {len(all_forecasts)} total forecasts")
    print(f"{'=' * 70}")
    print(f"\nExpected: {len(forecast_dates)} dates × 3 types × 4 horizons = {len(forecast_dates) * 3 * 4}")
    print(f"Actual: {len(all_forecasts)}")
    
    # Generate recommendations
    print("\nGenerating recommendations for high-risk forecasts...")
    recommendations = generate_all_recommendations(db, min_probability=0.3)
    print(f"✓ Created {len(recommendations)} recommendations")
    
    # Show high-risk forecasts
    high_risk = [f for f in all_forecasts if f.probability > 0.3]
    if high_risk:
        print(f"\n⚠️  {len(high_risk)} HIGH-RISK forecasts (>30% probability)")
    
    print("\n🎉 Now refresh your dashboard - you should see lines in the chart!")
    print("   Dashboard: http://localhost:3000/dashboard/forecasts")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
