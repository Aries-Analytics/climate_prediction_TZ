#!/usr/bin/env python3
"""
Debug script for forecast generation issue
Checks climate data availability and coordinate matching
"""

import sys
import os
from datetime import date, timedelta

# Add paths
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)
backend_dir = os.path.join(root_dir, 'backend')
if os.path.exists(backend_dir):
    sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal
from app.models.climate_data import ClimateData
from app.models.location import Location

def main():
    print("=" * 60)
    print("FORECAST GENERATION DEBUG")
    print("=" * 60)
    
    db = SessionLocal()
    
    # Get Morogoro location
    morogoro = db.query(Location).filter(Location.name == 'Morogoro').first()
    if not morogoro:
        print("ERROR: Morogoro location not found!")
        return
    
    print(f"\n1. Morogoro Location:")
    print(f"   Coordinates: ({morogoro.latitude}, {morogoro.longitude})")
    
    # Check total climate data
    total_records = db.query(ClimateData).count()
    print(f"\n2. Total Climate Data Records: {total_records}")
    
    # Check forecast base date (latest climate data)
    from sqlalchemy import func
    latest_date = db.query(func.max(ClimateData.date)).scalar()
    print(f"\n3. Latest Climate Data Date: {latest_date}")
    print(f"   Today: {date.today()}")
    print(f"   Data Age: {(date.today() - latest_date).days} days")
    
    # Check lookback period (180 days from latest_date)
    base_date = latest_date
    lookback_date = base_date - timedelta(days=180)
    print(f"\n4. Forecast Generation Parameters:")
    print(f"   Base Date: {base_date}")
    print(f"   Lookback Start: {lookback_date}")
    print(f"   Need: 30+ records in this period")
    
    # Check Morogoro records in lookback period
    tolerance = 0.001
    morogoro_records = db.query(ClimateData).filter(
        ClimateData.date >= lookback_date,
        ClimateData.date <= base_date,
        ClimateData.location_lat >= morogoro.latitude - tolerance,
        ClimateData.location_lat <= morogoro.latitude + tolerance,
        ClimateData.location_lon >= morogoro.longitude - tolerance,
        ClimateData.location_lon <= morogoro.longitude + tolerance
    ).all()
    
    print(f"\n5. Morogoro Records in Lookback Period:")
    print(f"   Found: {len(morogoro_records)} records")
    print(f"   Status: {'✅ SUFFICIENT' if len(morogoro_records) >= 30 else '❌ INSUFFICIENT'}")
    
    if morogoro_records:
        dates = sorted(set([r.date for r in morogoro_records]))
        print(f"   Date Range: {dates[0]} to {dates[-1]}")
        print(f"   Sample Coordinates: ({morogoro_records[0].location_lat}, {morogoro_records[0].location_lon})")
        
        # Show monthly distribution
        from collections import Counter
        monthly = Counter([f"{r.date.year}-{r.date.month:02d}" for r in morogoro_records])
        print(f"\n6. Monthly Distribution:")
        for month in sorted(monthly.keys()):
            print(f"   {month}: {monthly[month]} records")
    
    # Check all locations for comparison
    all_locations = db.query(Location).all()
    print(f"\n7. Records by Location (last 180 days):")
    for loc in all_locations:
        loc_records = db.query(ClimateData).filter(
            ClimateData.date >= lookback_date,
            ClimateData.date <= base_date,
            ClimateData.location_lat >= loc.latitude - tolerance,
            ClimateData.location_lat <= loc.latitude + tolerance,
            ClimateData.location_lon >= loc.longitude - tolerance,
            ClimateData.location_lon <= loc.longitude + tolerance
        ).count()
        status = "✅" if loc_records >= 30 else "❌"
        print(f"   {status} {loc.name}: {loc_records} records")
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS:")
    print("=" * 60)
    if len(morogoro_records) < 30:
        print("❌ PROBLEM: Insufficient climate data for forecasting")
        print(f"   Have: {len(morogoro_records)} records")
        print(f"   Need: 30+ records")
        print("\nROOT CAUSE:")
        print("   Climate data appears to be monthly (not daily)")
        print(f"   6 months of monthly data = only 6 records")
        print(f"   180 days lookback needs ~180 daily records OR consistent monthly data")
        print("\nSOLUTIONS:")
        print("   1. Use monthly data with shorter lookback (e.g., 6 months = 6 records)")
        print("   2. Convert monthly data to daily (forward fill)")
        print("   3. Adjust prepare_features to work with monthly cadence")
    else:
        print("✅ Data looks sufficient - check other issues")
    
    db.close()

if __name__ == "__main__":
    main()
