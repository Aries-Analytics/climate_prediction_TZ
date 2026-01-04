"""
Generate forecast timeline - creates forecasts from multiple dates

This creates a timeline of forecasts so you can see:
1. How predictions change over time
2. Lines connecting forecast points in the dashboard
3. Trends in risk predictions

IMPORTANT: 
- Forecast Date = When we make the forecast (needs climate data)
- Target Date = Future date we're predicting (3-6 months ahead)
- Example: Forecast from Nov 1, 2025 → predicts Feb-Apr 2026
"""
from app.core.database import SessionLocal
from app.services.forecast_service import generate_forecasts, generate_all_recommendations
from app.models.climate_data import ClimateData
from sqlalchemy import func
from datetime import date, timedelta

def main():
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("FORECAST TIMELINE GENERATION")
        print("=" * 70)
        
        # Find the latest climate data date
        latest_climate_date = db.query(func.max(ClimateData.date)).scalar()
        
        if not latest_climate_date:
            print("\n❌ No climate data found in database")
            print("Run the data ingestion pipeline first")
            return
        
        print(f"\nLatest climate data: {latest_climate_date}")
        print(f"We can generate forecasts up to this date")
        print(f"These forecasts will predict 3-6 months into the FUTURE\n")
        
        # Generate forecasts for the past 8 weeks (every week)
        # This creates a timeline showing how predictions evolved
        forecast_dates = []
        start_date = latest_climate_date - timedelta(weeks=8)
        
        for week in range(9):  # 9 data points (every week for 8 weeks)
            forecast_date = start_date + timedelta(weeks=week)
            # Only use dates where we have climate data
            if forecast_date <= latest_climate_date:
                forecast_dates.append(forecast_date)
        
        print(f"Generating forecasts for {len(forecast_dates)} dates...")
        print(f"Forecast date range: {forecast_dates[0]} to {forecast_dates[-1]}")
        
        # Show what future dates we'll be predicting
        earliest_target = forecast_dates[0] + timedelta(days=90)  # 3 months ahead
        latest_target = forecast_dates[-1] + timedelta(days=180)  # 6 months ahead
        print(f"Target predictions: {earliest_target} to {latest_target}")
        print(f"\nThis will create LINES in your chart! 🎉\n")
        
        print("=" * 70)
        
        total_generated = 0
        for i, forecast_date in enumerate(forecast_dates, 1):
            target_start = forecast_date + timedelta(days=90)  # 3 months
            target_end = forecast_date + timedelta(days=180)   # 6 months
            
            print(f"\n[{i}/{len(forecast_dates)}] Forecast from {forecast_date}")
            print(f"      → Predicting {target_start} to {target_end}")
            
            try:
                forecasts = generate_forecasts(
                    db, 
                    start_date=forecast_date, 
                    horizons=[3, 4, 5, 6]
                )
                print(f"      ✓ Generated {len(forecasts)} forecasts")
                total_generated += len(forecasts)
            except Exception as e:
                print(f"      ✗ Error: {e}")
        
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"✅ Total forecasts generated: {total_generated}")
        print(f"   Expected: {len(forecast_dates)} dates × 3 types × 4 horizons = {len(forecast_dates) * 3 * 4}")
        
        # Generate recommendations for high-risk forecasts
        print("\nGenerating recommendations for high-risk forecasts...")
        try:
            recommendations = generate_all_recommendations(db, min_probability=0.3)
            print(f"✓ Generated {len(recommendations)} recommendations")
        except Exception as e:
            print(f"✗ Error generating recommendations: {e}")
        
        print("\n" + "=" * 70)
        print("WHAT THIS MEANS FOR YOUR DASHBOARD:")
        print("=" * 70)
        print("✓ You'll now see LINES connecting forecast points")
        print("✓ Each line shows how predictions evolved over time")
        print("✓ Different line styles = different horizons (3-6 months)")
        print("✓ Different colors = different trigger types")
        print("\nRefresh your Early Warning System dashboard to see the timeline!")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
