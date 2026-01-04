"""
Generate real forecasts using actual climate data from the last 180 days.

This script:
1. Fetches the last 180 days of data from all 5 data sources (CHIRPS, NASA POWER, ERA5, NDVI, Ocean Indices)
2. Processes and merges the data
3. Loads the trained ML model
4. Generates forecasts for 3, 4, 5, and 6 months ahead
5. Stores forecasts in the database
"""
import sys
import os
from datetime import date, datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.database import SessionLocal
from app.services.forecast_service import generate_forecasts, generate_all_recommendations
from app.models.climate_data import ClimateData


def fetch_recent_data():
    """
    Fetch the last 180 days of data from all 5 data sources.
    
    Returns:
        dict: Dictionary with data from each source
    """
    print("\n" + "=" * 60)
    print("FETCHING LAST 180 DAYS OF CLIMATE DATA")
    print("=" * 60)
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    print(f"\nDate range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Total days: 180 (~6 months)")
    
    # Import ingestion modules
    from modules.ingestion import chirps_ingestion, nasa_power_ingestion, era5_ingestion, ndvi_ingestion, ocean_indices_ingestion
    
    data_sources = {}
    
    # 1. Fetch CHIRPS (rainfall) data
    print("\n[1/5] Fetching CHIRPS rainfall data...")
    try:
        chirps_data = chirps_ingestion.fetch_chirps_data(
            start_year=start_date.year,
            end_year=end_date.year,
            use_gee=True
        )
        # Filter to last 180 days
        chirps_data['date'] = chirps_data.apply(lambda row: datetime(int(row['year']), int(row['month']), 1), axis=1)
        chirps_data = chirps_data[chirps_data['date'] >= start_date]
        data_sources['chirps'] = chirps_data
        print(f"✓ Fetched {len(chirps_data)} CHIRPS records")
    except Exception as e:
        print(f"⚠️  CHIRPS fetch failed: {e}")
        data_sources['chirps'] = None
    
    # 2. Fetch NASA POWER (temperature, solar radiation) data
    print("\n[2/5] Fetching NASA POWER data...")
    try:
        nasa_data = nasa_power_ingestion.fetch_nasa_power_data(
            start_year=start_date.year,
            end_year=end_date.year
        )
        # Filter to last 180 days
        nasa_data['date'] = nasa_data.apply(lambda row: datetime(int(row['year']), int(row['month']), 1), axis=1)
        nasa_data = nasa_data[nasa_data['date'] >= start_date]
        data_sources['nasa_power'] = nasa_data
        print(f"✓ Fetched {len(nasa_data)} NASA POWER records")
    except Exception as e:
        print(f"⚠️  NASA POWER fetch failed: {e}")
        data_sources['nasa_power'] = None
    
    # 3. Fetch ERA5 (atmospheric variables) data
    print("\n[3/5] Fetching ERA5 data...")
    try:
        era5_data = era5_ingestion.fetch_era5_data(
            start_year=start_date.year,
            end_year=end_date.year
        )
        # Filter to last 180 days
        era5_data['date'] = era5_data.apply(lambda row: datetime(int(row['year']), int(row['month']), 1), axis=1)
        era5_data = era5_data[era5_data['date'] >= start_date]
        data_sources['era5'] = era5_data
        print(f"✓ Fetched {len(era5_data)} ERA5 records")
    except Exception as e:
        print(f"⚠️  ERA5 fetch failed: {e}")
        data_sources['era5'] = None
    
    # 4. Fetch NDVI (vegetation health) data
    print("\n[4/5] Fetching NDVI data...")
    try:
        ndvi_data = ndvi_ingestion.fetch_ndvi_data(
            start_year=start_date.year,
            end_year=end_date.year,
            use_gee=True
        )
        # Filter to last 180 days
        ndvi_data['date'] = ndvi_data.apply(lambda row: datetime(int(row['year']), int(row['month']), 1), axis=1)
        ndvi_data = ndvi_data[ndvi_data['date'] >= start_date]
        data_sources['ndvi'] = ndvi_data
        print(f"✓ Fetched {len(ndvi_data)} NDVI records")
    except Exception as e:
        print(f"⚠️  NDVI fetch failed: {e}")
        data_sources['ndvi'] = None
    
    # 5. Fetch Ocean Indices (ENSO, IOD) data
    print("\n[5/5] Fetching Ocean Indices data...")
    try:
        ocean_data = ocean_indices_ingestion.fetch_ocean_indices_data(
            start_year=start_date.year,
            end_year=end_date.year
        )
        # Filter to last 180 days
        ocean_data['date'] = ocean_data.apply(lambda row: datetime(int(row['year']), int(row['month']), 1), axis=1)
        ocean_data = ocean_data[ocean_data['date'] >= start_date]
        data_sources['ocean_indices'] = ocean_data
        print(f"✓ Fetched {len(ocean_data)} Ocean Indices records")
    except Exception as e:
        print(f"⚠️  Ocean Indices fetch failed: {e}")
        data_sources['ocean_indices'] = None
    
    return data_sources


def expand_monthly_to_daily(df):
    """
    Expand monthly data to daily data by forward-filling values.
    
    Args:
        df: DataFrame with monthly data
        
    Returns:
        DataFrame with daily data
    """
    import pandas as pd
    
    # Create a date range for all days in the period
    if df.empty:
        return df
    
    min_date = df['date'].min()
    max_date = df['date'].max()
    
    # Create daily date range
    daily_dates = pd.date_range(start=min_date, end=max_date, freq='D')
    daily_df = pd.DataFrame({'date': daily_dates})
    
    # Merge with monthly data and forward-fill
    merged = pd.merge(daily_df, df, on='date', how='left')
    
    # Forward fill the values (each month's value applies to all days in that month)
    merged = merged.ffill(axis=0)
    
    return merged


def merge_and_store_data(db, data_sources):
    """
    Merge data from all sources and store in database.
    
    Args:
        db: Database session
        data_sources: Dictionary with data from each source
        
    Returns:
        int: Number of records stored
    """
    print("\n" + "=" * 60)
    print("MERGING AND STORING DATA")
    print("=" * 60)
    
    import pandas as pd
    
    # Start with the first available dataset
    merged = None
    for source_name, df in data_sources.items():
        if df is not None and not df.empty:
            if merged is None:
                merged = df.copy()
                print(f"\nStarting with {source_name}: {len(df)} records")
            else:
                # Merge on year and month
                merged = pd.merge(merged, df, on=['year', 'month'], how='outer', suffixes=('', f'_{source_name}'))
                print(f"Merged {source_name}: {len(merged)} records")
    
    if merged is None or merged.empty:
        print("\n❌ No data to merge")
        return 0
    
    # Create date column if not exists (use first day of month)
    if 'date' not in merged.columns:
        merged['date'] = merged.apply(lambda row: datetime(int(row['year']), int(row['month']), 1), axis=1)
    
    # Expand monthly data to daily data
    print("\nExpanding monthly data to daily records...")
    merged = expand_monthly_to_daily(merged)
    print(f"Expanded to {len(merged)} daily records")
    
    # Map columns to ClimateData model fields
    records_stored = 0
    
    for _, row in merged.iterrows():
        try:
            # Check if record already exists
            existing = db.query(ClimateData).filter(
                ClimateData.date == row['date'].date()
            ).first()
            
            if existing:
                # Update existing record
                climate_data = existing
            else:
                # Create new record
                climate_data = ClimateData(date=row['date'].date())
            
            # Map data from sources
            # CHIRPS - rainfall
            if 'rainfall_mm' in row and pd.notna(row['rainfall_mm']):
                climate_data.rainfall_mm = float(row['rainfall_mm'])
            
            # NASA POWER - temperature
            if 't2m' in row and pd.notna(row['t2m']):
                climate_data.temperature_avg = float(row['t2m'])
            elif 'temperature' in row and pd.notna(row['temperature']):
                climate_data.temperature_avg = float(row['temperature'])
            
            # NDVI - vegetation health
            if 'ndvi' in row and pd.notna(row['ndvi']):
                climate_data.ndvi = float(row['ndvi'])
            
            # Ocean Indices - ENSO and IOD
            if 'oni' in row and pd.notna(row['oni']):
                climate_data.enso_index = float(row['oni'])
            if 'iod' in row and pd.notna(row['iod']):
                climate_data.iod_index = float(row['iod'])
            
            if not existing:
                db.add(climate_data)
            
            records_stored += 1
            
        except Exception as e:
            print(f"⚠️  Error storing record for {row['date']}: {e}")
            continue
    
    db.commit()
    print(f"\n✓ Stored {records_stored} climate data records in database")
    
    return records_stored


def main():
    """Generate real forecasts from recent climate data"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("REAL-TIME FORECAST GENERATION")
        print("=" * 60)
        print("\nThis script will:")
        print("1. Fetch last 180 days of data from all 5 sources")
        print("2. Process and merge the data")
        print("3. Store in database")
        print("4. Generate forecasts using trained ML model")
        
        # Step 1: Fetch recent data from all sources
        data_sources = fetch_recent_data()
        
        # Check if we got any data
        valid_sources = sum(1 for df in data_sources.values() if df is not None and not df.empty)
        if valid_sources == 0:
            print("\n❌ No data fetched from any source")
            return
        
        print(f"\n✓ Successfully fetched data from {valid_sources}/5 sources")
        
        # Step 2: Merge and store data
        records_stored = merge_and_store_data(db, data_sources)
        
        if records_stored == 0:
            print("\n❌ No data stored in database")
            return
        
        # Step 3: Generate forecasts for multiple dates (creates timeline)
        print("\n" + "=" * 60)
        print("GENERATING FORECAST TIMELINE")
        print("=" * 60)
        
        # Find the latest climate data date
        from sqlalchemy import func
        latest_climate_date = db.query(func.max(ClimateData.date)).scalar()
        
        if not latest_climate_date:
            print("\n❌ No climate data found in database")
            return
        
        print(f"\nLatest climate data: {latest_climate_date}")
        print("Note: Forecasts predict FUTURE dates (3-6 months ahead)")
        print("      We can only generate forecasts up to the latest data date\n")
        
        # Generate forecasts for the past 8 weeks (every week) to create a timeline
        # This shows how predictions evolved over time
        forecast_dates = []
        start_date = latest_climate_date - timedelta(weeks=8)
        
        for week in range(9):  # 0 to 8 weeks ago (9 data points)
            forecast_date = start_date + timedelta(weeks=week)
            # Only use dates where we have climate data
            if forecast_date <= latest_climate_date:
                forecast_dates.append(forecast_date)
        
        print(f"Generating forecasts for {len(forecast_dates)} dates...")
        print(f"Forecast date range: {forecast_dates[0]} to {forecast_dates[-1]}")
        
        # Calculate what dates we're predicting
        target_start = forecast_dates[0] + timedelta(days=90)  # 3 months ahead
        target_end = forecast_dates[-1] + timedelta(days=180)   # 6 months ahead
        print(f"These will predict: {target_start} to {target_end}\n")
        
        print("Loading trained model...")
        
        # Generate forecasts for all dates
        horizons = [3, 4, 5, 6]
        all_forecasts = []
        
        for forecast_date in forecast_dates:
            target_start = forecast_date + timedelta(days=90)
            target_end = forecast_date + timedelta(days=180)
            print(f"Forecast from {forecast_date} → predicting {target_start} to {target_end}")
            
            try:
                forecasts = generate_forecasts(db, forecast_date, horizons)
                print(f"  ✓ Generated {len(forecasts)} forecasts")
                all_forecasts.extend(forecasts)
            except Exception as e:
                print(f"  ✗ Error: {e}")
        
        forecasts = all_forecasts
        
        if not forecasts:
            print("\n❌ No forecasts generated")
            print("\nPossible reasons:")
            print("  - Insufficient climate data (need at least 30 days)")
            print("  - Model file not found or failed to load")
            return
        
        print(f"\n✓ Generated {len(forecasts)} forecasts")
        
        # Display forecast summary by trigger type
        print("\n" + "=" * 60)
        print("FORECAST SUMMARY")
        print("=" * 60)
        
        for trigger_type in ['drought', 'flood', 'crop_failure']:
            type_forecasts = [f for f in forecasts if f.trigger_type == trigger_type]
            if type_forecasts:
                avg_prob = sum(f.probability for f in type_forecasts) / len(type_forecasts)
                high_risk = sum(1 for f in type_forecasts if f.probability > 0.3)
                max_prob = max(f.probability for f in type_forecasts)
                
                print(f"\n{trigger_type.upper().replace('_', ' ')}:")
                print(f"  Average probability: {avg_prob:.1%}")
                print(f"  Maximum probability: {max_prob:.1%}")
                print(f"  High-risk forecasts (>30%): {high_risk}/{len(type_forecasts)}")
        
        # Generate recommendations for high-risk forecasts
        print("\n" + "=" * 60)
        print("GENERATING RECOMMENDATIONS")
        print("=" * 60)
        
        recommendations = generate_all_recommendations(db, min_probability=0.3)
        print(f"\n✓ Created {len(recommendations)} recommendations")
        
        # Display high-risk forecasts
        high_risk_forecasts = [f for f in forecasts if f.probability > 0.3]
        
        if high_risk_forecasts:
            print("\n" + "=" * 60)
            print(f"⚠️  HIGH-RISK FORECASTS ({len(high_risk_forecasts)} events with >30% probability)")
            print("=" * 60)
            
            for f in sorted(high_risk_forecasts, key=lambda x: x.probability, reverse=True):
                print(f"\n{f.trigger_type.upper().replace('_', ' ')}:")
                print(f"  Probability: {f.probability:.1%}")
                print(f"  Confidence Interval: [{f.confidence_lower:.1%}, {f.confidence_upper:.1%}]")
                print(f"  Horizon: {f.horizon_months} months ahead")
                print(f"  Target Date: {f.target_date}")
        else:
            print("\n✓ No high-risk forecasts (all probabilities < 30%)")
        
        print("\n" + "=" * 60)
        print("✓ FORECAST GENERATION COMPLETE!")
        print("=" * 60)
        print(f"\nData Summary:")
        print(f"  - Climate records stored: {records_stored}")
        print(f"  - Forecasts generated: {len(forecasts)}")
        print(f"  - Recommendations created: {len(recommendations)}")
        print("\nRefresh the Early Warning System dashboard to see the forecasts.")
        print("Dashboard URL: http://localhost:3000/dashboard/forecasts")
        
    except Exception as e:
        print(f"\n❌ Error generating forecasts: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == '__main__':
    main()
